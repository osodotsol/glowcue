from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.config import Settings


def make(**kwargs) -> Settings:
    # _env_file=None isolates tests from the developer's real backend/.env
    return Settings(_env_file=None, **kwargs)


def test_defaults_are_safe():
    s = make()
    assert s.youcam_mode == "mock"
    assert s.live_analysis_enabled is False
    assert s.currency == "NGN"
    assert s.credit_floor == 100


def test_live_mode_without_key_fails_fast():
    with pytest.raises(ValidationError, match="requires YOUCAM_API_KEY"):
        make(youcam_mode="live")


def test_live_mode_with_blank_key_fails_fast():
    with pytest.raises(ValidationError):
        make(youcam_mode="live", youcam_api_key="   ")


def test_secret_is_not_exposed_in_repr():
    s = make(youcam_mode="live", youcam_api_key="placeholder-value-for-test")
    assert "placeholder-value-for-test" not in repr(s)
    assert "placeholder-value-for-test" not in str(s.model_dump())


def test_cors_origins_include_configured_frontend():
    s = make(frontend_origin="https://glowcue.vercel.app")
    assert "https://glowcue.vercel.app" in s.cors_origins
    assert "http://localhost:5173" in s.cors_origins


def test_cors_development_allows_local_dev_origins():
    s = make(frontend_origin="https://glowcue.example")
    assert s.app_env == "development"
    assert set(s.cors_origins) == {"https://glowcue.example", "http://localhost:5173", "http://127.0.0.1:5173"}


def test_cors_production_allows_only_the_configured_frontend():
    s = make(app_env="production", frontend_origin="https://glowcue.example")
    assert s.cors_origins == ["https://glowcue.example"]


@pytest.mark.parametrize("origin", ["http://localhost:5173", "http://127.0.0.1:5173", "http://localhost"])
def test_cors_production_refuses_a_localhost_frontend_origin(origin):
    with pytest.raises(ValidationError, match="APP_ENV=production requires FRONTEND_ORIGIN"):
        make(app_env="production", frontend_origin=origin)


def test_cors_production_middleware_rejects_localhost_and_accepts_the_frontend(monkeypatch):
    from fastapi.testclient import TestClient

    from app.config import get_settings
    from app.main import create_app

    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("FRONTEND_ORIGIN", "https://glowcue.example")
    get_settings.cache_clear()
    client = TestClient(create_app())

    def preflight(origin: str):
        headers = {"Origin": origin, "Access-Control-Request-Method": "POST"}
        return client.options("/api/recommendations", headers=headers)

    assert preflight("https://glowcue.example").headers.get("access-control-allow-origin") == "https://glowcue.example"
    assert "access-control-allow-origin" not in preflight("http://localhost:5173").headers
    simple = client.get("/api/config", headers={"Origin": "http://localhost:5173"})
    assert "access-control-allow-origin" not in simple.headers


def test_cors_development_middleware_still_allows_the_local_frontend(monkeypatch):
    from fastapi.testclient import TestClient

    from app.config import get_settings
    from app.main import create_app

    monkeypatch.delenv("APP_ENV", raising=False)
    get_settings.cache_clear()
    client = TestClient(create_app())
    resp = client.get("/api/config", headers={"Origin": "http://localhost:5173"})
    assert resp.headers.get("access-control-allow-origin") == "http://localhost:5173"
