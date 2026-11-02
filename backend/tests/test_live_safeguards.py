"""Regression tests for the live-call safeguards B1-B6 (docs/SECURITY_PRIVACY.md 4.4)."""

from __future__ import annotations

import logging
from pathlib import Path

import httpx
import pytest
from fastapi.testclient import TestClient
from tests.youcam_fakes import FAKE_KEY, live_settings, selfie_bytes

from app.config import Settings
from app.main import _log_startup, create_app
from app.services.normalize import SD_ACTIONS
from app.services.youcam_client import LiveCallRefused, YouCamClient, live_refusal

APP_DIR = Path(__file__).resolve().parents[1] / "app"


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


def _py_files_containing(text: str) -> set[str]:
    return {p.relative_to(APP_DIR).as_posix() for p in APP_DIR.rglob("*.py") if text in p.read_text(encoding="utf-8")}


# ---------------------------------------------------------------------------------------------- B1
def test_settings_dotenv_outranks_environment_for_live_switches(tmp_path, monkeypatch):
    env_file = tmp_path / ".env"
    env_file.write_text("YOUCAM_MODE=mock\nLIVE_ANALYSIS_ENABLED=false\n", encoding="utf-8")
    monkeypatch.setenv("YOUCAM_MODE", "live")
    monkeypatch.setenv("LIVE_ANALYSIS_ENABLED", "true")
    monkeypatch.setenv("YOUCAM_API_KEY", FAKE_KEY)
    s = Settings(_env_file=env_file)
    assert s.youcam_mode == "mock" and s.live_analysis_enabled is False
    assert live_refusal(s) is not None


def test_settings_environment_applies_when_there_is_no_dotenv(monkeypatch):
    # Production (Render) has no .env file: its environment variables must still work.
    monkeypatch.setenv("YOUCAM_MODE", "live")
    monkeypatch.setenv("LIVE_ANALYSIS_ENABLED", "true")
    monkeypatch.setenv("YOUCAM_API_KEY", FAKE_KEY)
    s = Settings(_env_file=None)
    assert s.youcam_mode == "live" and live_refusal(s) is None


# ---------------------------------------------------------------------------------------------- B2
def test_only_the_youcam_client_mentions_the_youcam_host():
    assert _py_files_containing("makeupar") == {"services/youcam_client.py"}


def test_only_the_youcam_client_creates_http_clients():
    assert _py_files_containing("httpx") == {"services/youcam_client.py"}


@pytest.mark.anyio
async def test_live_mode_without_the_kill_switch_is_refused_before_any_request():
    calls: list[httpx.Request] = []
    settings = live_settings(live_analysis_enabled=False)
    async with YouCamClient(settings, transport=httpx.MockTransport(lambda r: calls.append(r))) as client:
        with pytest.raises(LiveCallRefused, match="LIVE_ANALYSIS_ENABLED"):
            await client.analyse_skin(selfie_bytes(), "image/jpeg", SD_ACTIONS)
    assert calls == []


# ---------------------------------------------------------------------------------------------- B3
@pytest.mark.anyio
async def test_mock_mode_client_never_uses_a_transport_even_if_given_one():
    calls: list[httpx.Request] = []
    settings = Settings(_env_file=None)  # mock mode
    async with YouCamClient(settings, transport=httpx.MockTransport(lambda r: calls.append(r))) as client:
        with pytest.raises(LiveCallRefused):
            await client.analyse_skin(selfie_bytes(), "image/jpeg", SD_ACTIONS)
        with pytest.raises(LiveCallRefused):
            await client.credit_balance()
    assert calls == []


# ---------------------------------------------------------------------------------------------- B4
def test_startup_log_reports_mode_and_key_presence_without_the_key():
    records: list[logging.LogRecord] = []
    handler = logging.Handler()
    handler.emit = records.append  # type: ignore[method-assign]
    logger = logging.getLogger("glowcue")
    logger.addHandler(handler)
    try:
        _log_startup(live_settings())
        _log_startup(Settings(_env_file=None))
    finally:
        logger.removeHandler(handler)
    on, off = (r.getMessage() for r in records[-2:])
    assert "YOUCAM_MODE=live" in on and "API key present" in on and "live analysis ON" in on
    assert "YOUCAM_MODE=mock" in off and "API key absent" in off and "live analysis OFF" in off
    assert all(FAKE_KEY not in r.getMessage() for r in records)


# ---------------------------------------------------------------------------------------------- B6
def test_live_analysis_is_off_by_default():
    s = Settings(_env_file=None)
    assert s.youcam_mode == "mock" and s.live_analysis_enabled is False and live_refusal(s) is not None


def test_default_server_refuses_live_uploads_and_reports_live_disabled():
    client = TestClient(create_app())
    assert client.get("/api/config").json()["live_enabled"] is False
    resp = client.post("/api/analyses?consent=true", content=selfie_bytes(), headers={"Content-Type": "image/jpeg"})
    assert resp.status_code == 503 and resp.json()["error"]["code"] == "live_unavailable"


def test_settings_api_key_is_never_in_repr_or_dump():
    s = live_settings()
    assert FAKE_KEY not in repr(s) and FAKE_KEY not in str(s.model_dump())
