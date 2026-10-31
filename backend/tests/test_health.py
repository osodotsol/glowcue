from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import create_app


def test_health_returns_ok_in_mock_mode(monkeypatch):
    monkeypatch.setenv("YOUCAM_MODE", "mock")
    from app.config import get_settings

    get_settings.cache_clear()
    client = TestClient(create_app())
    resp = client.get("/api/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok", "mode": "mock"}


def test_cors_allows_frontend_origin_only():
    from app.config import get_settings

    get_settings.cache_clear()
    client = TestClient(create_app())
    ok = client.get("/api/health", headers={"Origin": "http://localhost:5173"})
    assert ok.headers.get("access-control-allow-origin") == "http://localhost:5173"
    other = client.get("/api/health", headers={"Origin": "https://evil.example"})
    assert "access-control-allow-origin" not in other.headers
