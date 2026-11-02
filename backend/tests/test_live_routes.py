"""POST /api/analyses and GET /api/analyses/{id} with a fake YouCam (no network, no real key)."""

from __future__ import annotations

import io

import httpx
import pytest
from fastapi.testclient import TestClient
from PIL import Image
from tests.test_image import jpeg_with_metadata
from tests.youcam_fakes import FAKE_KEY, Clock, FakeYouCam, selfie_bytes

from app.config import get_settings
from app.main import create_app
from app.services.youcam_client import YouCamClient

JPEG = {"Content-Type": "image/jpeg"}


@pytest.fixture
def fake() -> FakeYouCam:
    return FakeYouCam()


@pytest.fixture
def live(monkeypatch, fake):
    """A live-mode app (fake key, kill switch on) whose YouCam client talks to the fake."""
    monkeypatch.setenv("YOUCAM_MODE", "live")
    monkeypatch.setenv("LIVE_ANALYSIS_ENABLED", "true")
    monkeypatch.setenv("YOUCAM_API_KEY", FAKE_KEY)
    get_settings.cache_clear()
    app = create_app()
    clock = Clock()
    app.state.youcam_factory = lambda s: YouCamClient(
        s, transport=httpx.MockTransport(fake), sleep=clock.sleep, clock=clock.time
    )
    return TestClient(app)


def submit(client: TestClient, body: bytes | None = None, consent: str | None = "true", headers=JPEG):
    url = "/api/analyses" + (f"?consent={consent}" if consent is not None else "")
    return client.post(url, content=body if body is not None else selfie_bytes(), headers=headers)


def test_live_routes_require_consent_before_reading_the_photo(live, fake):
    for consent in (None, "false"):
        resp = submit(live, body=b"not even an image", consent=consent)
        assert resp.status_code == 422 and resp.json()["error"]["code"] == "consent_required"
    assert fake.requests == []


def test_live_routes_reject_wrong_content_type(live):
    resp = submit(live, headers={"Content-Type": "image/gif"})
    assert resp.status_code == 415 and resp.json()["error"]["code"] == "invalid_image"


def test_live_routes_reject_a_fake_image_by_signature(live, fake):
    resp = submit(live, body=b"<html>definitely not a jpeg</html>")
    assert resp.status_code == 415 and resp.json()["error"]["code"] == "invalid_image"
    assert fake.requests == []


def test_live_routes_reject_oversized_uploads(live):
    resp = submit(live, body=b"\xff\xd8\xff" + b"0" * (10 * 1024 * 1024))
    assert resp.status_code == 413 and resp.json()["error"]["code"] == "image_too_large"


def test_live_routes_reject_small_photos(live):
    resp = submit(live, body=selfie_bytes((400, 400)))
    assert resp.status_code == 422 and resp.json()["error"]["code"] == "image_too_small"


def test_live_routes_success_returns_a_labelled_live_analysis(live, fake):
    accepted = submit(live, body=jpeg_with_metadata((900, 1200)))
    assert accepted.status_code == 202
    job = accepted.json()
    assert job["status"] == "running" and job["analysis_id"].startswith("live-")

    done = live.get(f"/api/analyses/{job['analysis_id']}").json()
    assert done["status"] == "success" and done["error"] is None
    analysis = done["analysis"]
    assert analysis["mode"] == "live" and analysis["is_demo"] is False and analysis["profile_id"] is None
    assert "YouCam" in analysis["notice"]
    scores = {m["key"]: m["raw_score"] for m in analysis["metrics"]}
    assert len(scores) == 9 and scores["dark_circles"] == 44.7


def test_live_routes_upload_only_metadata_free_jpeg_to_youcam(live, fake):
    submit(live, body=jpeg_with_metadata((900, 1200)))
    (upload,) = fake.uploads
    assert upload.content.startswith(b"\xff\xd8\xff")
    assert b"Exif" not in upload.content and b"SecretCameraMake" not in upload.content
    assert len(Image.open(io.BytesIO(upload.content)).getexif()) == 0


def test_live_routes_photo_problems_come_back_with_retake_guidance(live, fake):
    fake.task_error = "error_src_face_too_small"
    job = submit(live).json()
    done = live.get(f"/api/analyses/{job['analysis_id']}").json()
    assert done["status"] == "error" and done["analysis"] is None
    assert done["error"]["code"] == "face_too_small" and done["error"]["retake"] is True
    assert "closer" in done["error"]["message"]


def test_live_routes_service_problems_offer_a_sample_profile(live, fake):
    fake.balance = 50  # below the credit floor
    job = submit(live).json()
    error = live.get(f"/api/analyses/{job['analysis_id']}").json()["error"]
    assert error["code"] == "live_paused" and error["retake"] is False and "sample profile" in error["message"]
    assert fake.uploads == []


def test_live_routes_enforce_the_per_ip_daily_cap(monkeypatch, live):
    monkeypatch.setenv("PER_IP_PER_DAY", "2")
    get_settings.cache_clear()
    assert submit(live).status_code == 202
    assert submit(live).status_code == 202
    third = submit(live)
    assert third.status_code == 429 and third.json()["error"]["code"] == "daily_limit_reached"


def test_live_routes_enforce_the_global_daily_cap(monkeypatch, live):
    monkeypatch.setenv("MAX_LIVE_PER_DAY", "1")
    get_settings.cache_clear()
    assert submit(live).status_code == 202
    assert submit(live).status_code == 429


def test_live_routes_give_the_slot_back_when_youcam_does_not_bill(monkeypatch, live, fake):
    monkeypatch.setenv("PER_IP_PER_DAY", "1")
    get_settings.cache_clear()
    fake.task_error = "error_no_face"  # a failed task costs no units
    for _ in range(3):
        assert submit(live).status_code == 202


def test_live_routes_unknown_or_expired_id_is_404(live):
    resp = live.get("/api/analyses/live-does-not-exist")
    assert resp.status_code == 404 and resp.json()["error"]["code"] == "unknown_analysis"


def test_live_routes_keep_the_demo_available_in_live_mode(live):
    assert live.get("/api/config").json()["live_enabled"] is True
    demo = live.post("/api/analyses/demo", json={"profile_id": "balanced"}).json()
    assert demo["is_demo"] is True and demo["mode"] == "demo"


def test_live_routes_result_flows_into_recommendations(live):
    job = submit(live).json()
    analysis = live.get(f"/api/analyses/{job['analysis_id']}").json()["analysis"]
    body = {
        "metrics": [{"key": m["key"], "raw_score": m["raw_score"]} for m in analysis["metrics"]],
        "skin_type": analysis["skin_type"],
        "preferences": {"budget": 30000, "skin_type": "combination"},
    }
    result = live.post("/api/recommendations", json=body)
    assert result.status_code == 200
    priorities = {p["key"] for p in result.json()["priorities"] if p["band"] == "priority"}
    assert priorities == {"oiliness", "dark_circles", "pore"}  # the three lowest raw_scores, all under 60
