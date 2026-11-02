"""The interface every skin-analysis provider implements."""

from __future__ import annotations

from typing import Protocol

from app.models import CONCERN_LABELS, DemoProfile, NormalizedAnalysis

__all__ = ["CONCERN_LABELS", "SkinAnalysisProvider"]


class SkinAnalysisProvider(Protocol):
    """Turns an analysis request into GlowCue's NormalizedAnalysis.

    The demo provider takes a profile id and never receives a photo. A live provider will take image bytes
    (held in memory only) and must map vendor output onto the same NormalizedAnalysis shape.
    """

    name: str

    def profiles(self) -> list[DemoProfile]: ...

    def analyse_profile(self, profile_id: str) -> NormalizedAnalysis: ...
