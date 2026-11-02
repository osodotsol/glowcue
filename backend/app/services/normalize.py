"""YouCam output -> GlowCue NormalizedAnalysis. Pure functions: no I/O, time or randomness.

Only `raw_score` is used (higher = healthier-looking, 1-100, per the official docs). `ui_score` is ignored:
YouCam documents it as adjusted "to produce more favorable results". A concern YouCam did not return, or
returned with an unusable score, becomes `not_measured`; nothing is invented.
"""

from __future__ import annotations

import math
from collections.abc import Iterable
from dataclasses import dataclass
from typing import Protocol

from app.engine.concerns import assess
from app.models import CONCERN_LABELS, Metric, MetricInput, NormalizedAnalysis

# YouCam SD action -> GlowCue concern key. The internal keys (and the recommendation engine) are unchanged.
YOUCAM_TO_CONCERN: dict[str, str] = {
    "pore": "pore",
    "dark_circle_v2": "dark_circles",
    "age_spot": "age_spot",
    "moisture": "moisture",
    "oiliness": "oiliness",
    "texture": "texture",
    "redness": "redness",
    "wrinkle": "wrinkle",
    "acne": "acne",
}
# The nine SD actions requested (9 concerns = the 9-12 tier, 14 units). No HD, no skin_type, no masks.
SD_ACTIONS: tuple[str, ...] = tuple(YOUCAM_TO_CONCERN)

LIVE_PROVIDER = "YouCam AI Skin Analysis (SD), via GlowCue"
LIVE_NOTICE = (
    "Cosmetic analysis of your photo by YouCam (Perfect Corp). Scores run 1-100; higher means healthier-looking "
    "skin. Results depend on lighting and the photo, and are not medical advice."
)


class ScoredItem(Protocol):
    type: str
    region: str | None
    raw_score: float | None


@dataclass(frozen=True)
class Normalised:
    scores: dict[str, float | None]  # concern key -> raw_score, or None when not measured
    ignored_types: tuple[str, ...]  # returned types GlowCue does not use (e.g. all, skin_age)


def _usable(score: float | None) -> float | None:
    if score is None or not math.isfinite(score) or not 1 <= score <= 100:
        return None
    return float(score)


def normalise_items(items: Iterable[ScoredItem]) -> Normalised:
    """Pick one raw_score per concern. If a type appears per region, the whole-face (or region-less) item wins."""
    chosen: dict[str, ScoredItem] = {}
    ignored: list[str] = []
    for item in items:
        key = YOUCAM_TO_CONCERN.get(item.type)
        if key is None:
            if item.type not in ignored:
                ignored.append(item.type)
            continue
        whole = item.region in (None, "", "whole")
        current = chosen.get(key)
        if current is None or (whole and current.region not in (None, "", "whole")):
            chosen[key] = item
    scores = {key: _usable(chosen[key].raw_score) if key in chosen else None for key in CONCERN_LABELS}
    return Normalised(scores=scores, ignored_types=tuple(sorted(ignored)))


def build_live_analysis(analysis_id: str, normalised: Normalised) -> NormalizedAnalysis:
    """Same shape and banding as the demo provider, honestly labelled as a live result."""
    states = assess([MetricInput(key=k, raw_score=v) for k, v in normalised.scores.items()], [])
    bands = {s.key: s.band for s in states}
    metrics = [
        Metric(
            key=key,
            label=CONCERN_LABELS[key],
            raw_score=score,
            ui_score=round(score) if score is not None else None,  # GlowCue shows raw_score, rounded
            band=bands.get(key, "not_measured"),
        )
        for key, score in normalised.scores.items()
    ]
    return NormalizedAnalysis(
        analysis_id=analysis_id,
        mode="live",
        provider=LIVE_PROVIDER,
        is_demo=False,
        profile_id=None,
        metrics=metrics,
        skin_type=None,  # not requested: the customer's self-reported skin type is used instead
        notice=LIVE_NOTICE,
    )
