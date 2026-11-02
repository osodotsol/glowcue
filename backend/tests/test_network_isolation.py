"""Proof that tests cannot use the real YouCam key or reach the real network (security finding H2).

These tests exercise the autouse fixtures in conftest.py. They deliberately attempt "accidental live" requests
and assert that every route is blocked. No packet is ever sent: the block happens before any connection.
"""

from __future__ import annotations

import asyncio
import socket
import urllib.request

import httpx
import pytest
from conftest import LiveRequestBlocked
from fastapi.testclient import TestClient

from app.config import Settings, get_settings
from app.main import create_app

REAL_HOST = "https://yce-api-01." + "makeupar.com/s2s/v1.0/client/credit"


# ---------- credentials are isolated ----------
def test_settings_ignore_backend_env_file_in_tests():
    """Even when the owner's real backend/.env exists, tests see no key and mock mode."""
    assert Settings.model_config.get("env_file") is None
    settings = get_settings()
    assert settings.youcam_api_key is None
    assert settings.youcam_mode == "mock"
    assert settings.live_analysis_enabled is False


def test_process_environment_key_is_removed(monkeypatch):
    monkeypatch.setenv("YOUCAM_API_KEY", "placeholder-not-a-real-key")
    # The fixture ran BEFORE this monkeypatch, so prove the cache is cleared and a re-read sees only what we set.
    get_settings.cache_clear()
    assert get_settings().youcam_api_key is not None  # we injected it ourselves, explicitly, inside the test
    monkeypatch.delenv("YOUCAM_API_KEY")
    get_settings.cache_clear()
    assert get_settings().youcam_api_key is None


def test_default_settings_never_enable_live_mode():
    s = Settings(_env_file=None)
    assert (s.youcam_mode, s.live_analysis_enabled) == ("mock", False)


# ---------- real network is blocked ----------
def test_sync_httpx_to_real_host_is_blocked():
    with pytest.raises(LiveRequestBlocked), httpx.Client() as client:
        client.get(REAL_HOST, headers={"Authorization": "Bearer placeholder"})


def test_async_httpx_to_real_host_is_blocked():
    async def attempt():
        async with httpx.AsyncClient() as client:
            await client.get(REAL_HOST)

    with pytest.raises(LiveRequestBlocked):
        asyncio.run(attempt())


def test_raw_socket_to_real_host_is_blocked():
    with pytest.raises(LiveRequestBlocked):
        socket.create_connection(("yce-api-01." + "makeupar.com", 443), timeout=1)


def test_dns_lookup_of_real_host_is_blocked():
    with pytest.raises(LiveRequestBlocked):
        socket.getaddrinfo("yce-api-01." + "makeupar.com", 443)


def test_urllib_to_real_host_is_blocked():
    with pytest.raises(LiveRequestBlocked):
        urllib.request.urlopen(REAL_HOST, timeout=1)  # noqa: S310


def test_arbitrary_external_address_is_blocked():
    with pytest.raises(LiveRequestBlocked):
        socket.create_connection(("93.184.216.34", 80), timeout=1)


# ---------- legitimate test techniques still work ----------
def test_mock_transport_still_works():
    seen = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(str(request.url))
        return httpx.Response(200, json={"status": 200, "results": [{"amount": 1000}]})

    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        resp = client.get(REAL_HOST)
    assert resp.json()["results"][0]["amount"] == 1000
    assert seen == [REAL_HOST]  # the "request" never left the process


def test_async_mock_transport_still_works():
    async def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"ok": True})

    async def attempt():
        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
            return (await client.get(REAL_HOST)).json()

    assert asyncio.run(attempt()) == {"ok": True}


def test_fastapi_test_client_still_works():
    client = TestClient(create_app())
    assert client.get("/api/health").json() == {"status": "ok", "mode": "mock"}
