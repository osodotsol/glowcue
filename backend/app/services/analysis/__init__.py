"""Skin-analysis providers.

The demo provider (profile id in, fixed demonstration scores out, no photo) is ALWAYS available, also in live
mode, so customers can choose it explicitly. Live analysis of a photo is a separate path
(`services/analysis/live.py`), because it is asynchronous and image-based; it never falls back to demo data.
"""

from __future__ import annotations

from app.config import Settings
from app.services.analysis.base import SkinAnalysisProvider
from app.services.analysis.demo import DemoAnalysisProvider


def get_provider(settings: Settings) -> SkinAnalysisProvider:  # noqa: ARG001  (kept for a stable call site)
    return DemoAnalysisProvider()


__all__ = ["SkinAnalysisProvider", "get_provider"]
