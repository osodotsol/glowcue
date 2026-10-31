"""Shared test setup: always run in mock mode, never touch the developer's real .env values."""

from __future__ import annotations

import pytest


@pytest.fixture(autouse=True)
def _mock_mode(monkeypatch):
    monkeypatch.setenv("YOUCAM_MODE", "mock")
    monkeypatch.delenv("YOUCAM_API_KEY", raising=False)
    from app.config import get_settings

    get_settings.cache_clear()
    yield
    get_settings.cache_clear()
