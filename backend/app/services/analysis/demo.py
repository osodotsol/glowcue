"""Demo (mock) analysis provider.

It returns fixed, hand-written scores for a few illustrative skin profiles. It NEVER receives or inspects a
photo and makes no network calls. Every response says it is demonstration data.
"""

from __future__ import annotations

import uuid

from app.engine.concerns import assess
from app.errors import AppError
from app.models import DemoProfile, Metric, MetricInput, NormalizedAnalysis
from app.services.analysis.base import CONCERN_LABELS

DEMO_NOTICE = (
    "Demonstration data. These scores come from a GlowCue demo profile, not from an analysis of your photo. "
    "Your photo stayed in your browser."
)

# raw_score per concern: 1-100, higher = healthier-looking (same semantics as YouCam's raw_score).
_PROFILES: dict[str, dict] = {
    "shine-prone": {
        "name": "Shine-prone & congested",
        "summary": "Visible shine, larger-looking pores and occasional blemishes.",
        "skin_type": "oily",
        "scores": {
            "oiliness": 38, "moisture": 72, "texture": 61, "pore": 44, "acne": 52,
            "redness": 80, "age_spot": 70, "wrinkle": 86, "dark_circles": 74,
        },
    },
    "dry-sensitive": {
        "name": "Dry & easily irritated",
        "summary": "Feels tight, looks dull and shows some redness.",
        "skin_type": "dry",
        "scores": {
            "oiliness": 88, "moisture": 39, "texture": 58, "pore": 82, "acne": 85,
            "redness": 47, "age_spot": 73, "wrinkle": 69, "dark_circles": 71,
        },
    },
    "uneven-tone": {
        "name": "Uneven tone & tired eyes",
        "summary": "Dark spots, some rough texture and under-eye circles.",
        "skin_type": "combination",
        "scores": {
            "oiliness": 66, "moisture": 64, "texture": 49, "pore": 68, "acne": 78,
            "redness": 76, "age_spot": 41, "wrinkle": 72, "dark_circles": 45,
        },
    },
    "balanced": {
        "name": "Balanced",
        "summary": "No concern stands out; a simple maintenance routine fits.",
        "skin_type": "normal",
        "scores": {
            "oiliness": 81, "moisture": 79, "texture": 83, "pore": 78, "acne": 88,
            "redness": 84, "age_spot": 80, "wrinkle": 90, "dark_circles": 77,
        },
    },
}  # fmt: skip


class DemoAnalysisProvider:
    name = "GlowCue demo data (not a real skin analysis)"

    def profiles(self) -> list[DemoProfile]:
        return [DemoProfile(id=pid, name=p["name"], summary=p["summary"]) for pid, p in _PROFILES.items()]

    def analyse_profile(self, profile_id: str) -> NormalizedAnalysis:
        profile = _PROFILES.get(profile_id)
        if profile is None:
            raise AppError("unknown_profile", f"Unknown demo profile '{profile_id}'.", status=404)
        scores: dict[str, float] = profile["scores"]
        bands = {s.key: s.band for s in assess([MetricInput(key=k, raw_score=v) for k, v in scores.items()], [])}
        metrics = [
            Metric(key=key, label=CONCERN_LABELS[key], raw_score=score, ui_score=round(score), band=bands[key])
            for key, score in scores.items()
        ]
        return NormalizedAnalysis(
            analysis_id=f"demo-{uuid.uuid4()}",
            mode="demo",
            provider=self.name,
            is_demo=True,
            profile_id=profile_id,
            metrics=metrics,
            skin_type=profile["skin_type"],
            notice=DEMO_NOTICE,
        )
