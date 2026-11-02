"""POST /api/analyses: cheap checks first, capacity reserved before decoding, decoding off the event loop."""

from __future__ import annotations

import asyncio
import threading
import time

import httpx
import pytest
from fastapi.testclient import TestClient
from tests.youcam_fakes import FAKE_KEY, Clock, FakeYouCam, selfie_bytes

import app.routes.analysis as analysis_routes
from app.config import get_settings
from app.main import create_app
from app.services.image import prepare_image as real_prepare_image
from app.services.youcam_client import YouCamClient

JPEG = {"Content-Type": "image/jpeg"}


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


def make_app(monkeypatch, per_ip: int = 5, global_max: int = 25):
    monkeypatch.setenv("YOUCAM_MODE", "live")
    monkeypatch.setenv("LIVE_ANALYSIS_ENABLED", "true")
    monkeypatch.setenv("YOUCAM_API_KEY", FAKE_KEY)
    monkeypatch.setenv("PER_IP_PER_DAY", str(per_ip))
    monkeypatch.setenv("MAX_LIVE_PER_DAY", str(global_max))
    get_settings.cache_clear()
    app = create_app()
    clock = Clock()
    app.state.youcam_factory = lambda s: YouCamClient(
        s, transport=httpx.MockTransport(FakeYouCam()), sleep=clock.sleep, clock=clock.time
    )
    return app


@pytest.fixture
def decode_calls(monkeypatch) -> list[int]:
    """Counts real decodes by wrapping the route's prepare_image (the expensive step)."""
    calls: list[int] = []

    def spy(data: bytes):
        calls.append(len(data))
        return real_prepare_image(data)

    monkeypatch.setattr(analysis_routes, "prepare_image", spy)
    return calls


def post(client: TestClient, body: bytes, consent: str | None = "true", headers=JPEG):
    url = "/api/analyses" + (f"?consent={consent}" if consent is not None else "")
    return client.post(url, content=body, headers=headers)


def test_upload_rejections_happen_before_any_decoding_or_reservation(monkeypatch, decode_calls):
    client = TestClient(make_app(monkeypatch, per_ip=1))
    assert post(client, selfie_bytes(), consent=None).status_code == 422  # no consent
    assert post(client, selfie_bytes(), headers={"Content-Type": "image/gif"}).status_code == 415  # wrong type
    big = {"Content-Type": "image/jpeg", "Content-Length": str(11 * 1024 * 1024)}
    assert post(client, b"x", headers=big).status_code == 413  # declared too large
    assert post(client, b"<html>not an image</html>").status_code == 415  # wrong signature
    assert decode_calls == []
    assert post(client, selfie_bytes()).status_code == 202  # capacity (1) was never consumed by the rejections


def test_upload_invalid_image_releases_its_reservation(monkeypatch, decode_calls):
    client = TestClient(make_app(monkeypatch, per_ip=1))
    corrupt = b"\xff\xd8\xff" + b"\x00" * 2048  # passes the cheap signature check, fails decoding
    resp = post(client, corrupt)
    assert resp.status_code == 415 and resp.json()["error"]["code"] == "invalid_image"
    assert len(decode_calls) == 1
    assert post(client, selfie_bytes()).status_code == 202  # the slot came back


def test_upload_successful_reservation_is_held(monkeypatch, decode_calls):
    client = TestClient(make_app(monkeypatch, per_ip=1))
    assert post(client, selfie_bytes()).status_code == 202
    second = post(client, selfie_bytes())
    assert second.status_code == 429 and second.json()["error"]["code"] == "daily_limit_reached"


def test_upload_failed_reservation_skips_decoding(monkeypatch, decode_calls):
    client = TestClient(make_app(monkeypatch, per_ip=1))
    post(client, selfie_bytes())
    post(client, selfie_bytes())  # refused by the cap
    assert len(decode_calls) == 1  # only the accepted upload was decoded


def test_upload_global_cap_is_enforced_before_decoding(monkeypatch, decode_calls):
    client = TestClient(make_app(monkeypatch, per_ip=5, global_max=1))
    assert post(client, selfie_bytes()).status_code == 202
    assert post(client, selfie_bytes()).status_code == 429
    assert len(decode_calls) == 1


@pytest.mark.anyio
async def test_upload_concurrent_requests_never_exceed_capacity_or_leak_slots(monkeypatch):
    app = make_app(monkeypatch, per_ip=3)

    def slow_prepare(data: bytes):
        time.sleep(0.15)  # hold a decode slot long enough for requests to overlap
        return real_prepare_image(data)

    monkeypatch.setattr(analysis_routes, "prepare_image", slow_prepare)
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:

        async def one():
            return await client.post("/api/analyses?consent=true", content=selfie_bytes(), headers=JPEG)

        results = await asyncio.gather(*(one() for _ in range(6)))
        codes = sorted(r.status_code for r in results)
        accepted = codes.count(202)
        assert set(codes) <= {202, 429, 503}
        assert 1 <= accepted <= 3
        if 503 in codes:  # "busy": too many decodes at once, told to retry
            busy = [r for r in results if r.status_code == 503]
            assert all(r.json()["error"]["code"] == "busy" and r.json()["error"]["retryable"] for r in busy)

        # Exactly the unused capacity is still available: nothing was double-counted or left stuck.
        later = []
        for _ in range(4):
            r = await one()
            later.append(r.status_code)
        assert later.count(202) == 3 - accepted
        assert later[3 - accepted :] == [429] * (4 - (3 - accepted))


@pytest.mark.anyio
async def test_upload_decoding_runs_off_the_event_loop(monkeypatch):
    app = make_app(monkeypatch)
    loop_thread = threading.get_ident()
    decode_threads: list[int] = []

    def blocking_prepare(data: bytes):
        decode_threads.append(threading.get_ident())
        time.sleep(0.4)  # a slow, blocking decode
        return real_prepare_image(data)

    monkeypatch.setattr(analysis_routes, "prepare_image", blocking_prepare)
    transport = httpx.ASGITransport(app=app)
    ticks = 0
    done = asyncio.Event()

    async def heartbeat():
        nonlocal ticks
        while not done.is_set():
            ticks += 1
            await asyncio.sleep(0.02)

    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:

        async def upload():
            try:
                return await client.post("/api/analyses?consent=true", content=selfie_bytes(), headers=JPEG)
            finally:
                done.set()

        response, _ = await asyncio.gather(upload(), heartbeat())

    assert response.status_code == 202
    assert decode_threads and decode_threads[0] != loop_thread  # decoded in a worker thread
    assert ticks >= 8  # the event loop kept running during the 0.4 s decode (it would stall at ~1 tick)
