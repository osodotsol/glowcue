from __future__ import annotations

import pytest

from app.config import Settings
from app.errors import AppError
from app.models import CONCERN_KEYS
from app.services.analysis import get_provider
from app.services.analysis.demo import DemoAnalysisProvider


def test_mock_mode_selects_the_demo_provider():
    assert isinstance(get_provider(Settings()), DemoAnalysisProvider)


def test_demo_provider_labels_everything_as_demonstration_data():
    provider = DemoAnalysisProvider()
    for profile in provider.profiles():
        result = provider.analyse_profile(profile.id)
        assert result.is_demo is True
        assert result.mode == "demo"
        assert "demo" in result.provider.lower() and "not a real" in result.provider.lower()
        assert "not from an analysis of your photo" in result.notice
        assert "YouCam" not in result.provider  # never claim the vendor produced demo data


def test_demo_profiles_cover_all_nine_concerns_with_valid_scores():
    provider = DemoAnalysisProvider()
    for profile in provider.profiles():
        result = provider.analyse_profile(profile.id)
        assert {m.key for m in result.metrics} == set(CONCERN_KEYS)
        assert all(1 <= m.raw_score <= 100 for m in result.metrics)


def test_unknown_profile_is_a_404_error():
    with pytest.raises(AppError) as exc:
        DemoAnalysisProvider().analyse_profile("nope")
    assert exc.value.status == 404


def test_demo_provider_stays_available_in_live_mode():
    # Live analysis is a separate, photo-based path; the demo stories remain an explicit choice.
    settings = Settings(_env_file=None, youcam_mode="live", youcam_api_key="placeholder-not-a-key")
    assert isinstance(get_provider(settings), DemoAnalysisProvider)
