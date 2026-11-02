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
