"""Priorities and weights from scores (spec 9.2 steps 1-3).

Severity = 100 - raw_score (higher raw_score = healthier-looking). ui_score is never used for ranking.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.models import CONCERN_LABELS, MetricInput

PRIORITY_MAX_RAW = 60  # among the 3 most severe AND below this -> "priority"
WATCH_MAX_RAW = 75  # below this -> "watch"
SELF_REPORTED_MULTIPLIER = 1.5
SELF_REPORTED_MIN_SEVERITY = 20.0


@dataclass(frozen=True)
class ConcernState:
    key: str
    label: str
    raw_score: float | None
    severity: float
    band: str  # priority | watch | good | not_measured
    self_reported: bool

    @property
    def active(self) -> bool:
        return self.band in ("priority", "watch")


def assess(metrics: list[MetricInput], self_reported: list[str]) -> list[ConcernState]:
    """Band every concern. Customer-reported concerns are always at least 'watch'."""
    reported = set(self_reported)
    measured = sorted((m for m in metrics if m.raw_score is not None), key=lambda m: (-(100 - m.raw_score), m.key))
    top3 = {m.key for m in measured[:3]}
    states: list[ConcernState] = []
    for m in measured:
        raw = float(m.raw_score)
        if m.key in top3 and raw < PRIORITY_MAX_RAW:
            band = "priority"
        elif raw < WATCH_MAX_RAW or m.key in reported:
            band = "watch"
        else:
            band = "good"
        states.append(ConcernState(m.key, CONCERN_LABELS[m.key], raw, 100 - raw, band, m.key in reported))
    seen = {s.key for s in states}
    for key in sorted(reported - seen):  # reported but not measured: still worth covering
        states.append(ConcernState(key, CONCERN_LABELS[key], None, SELF_REPORTED_MIN_SEVERITY, "watch", True))
    for m in metrics:
        if m.raw_score is None and m.key not in reported:
            states.append(ConcernState(m.key, CONCERN_LABELS[m.key], None, 0.0, "not_measured", False))
    order = {"priority": 0, "watch": 1, "good": 2, "not_measured": 3}
    return sorted(states, key=lambda s: (order[s.band], -s.severity, s.key))


def weights(states: list[ConcernState]) -> dict[str, float]:
    """w_c = adjusted severity / total, over active concerns only. Empty dict -> maintenance routine."""
    raw: dict[str, float] = {}
    for s in states:
        if not s.active:
            continue
        severity = max(s.severity, SELF_REPORTED_MIN_SEVERITY) if s.self_reported else s.severity
        raw[s.key] = severity * (SELF_REPORTED_MULTIPLIER if s.self_reported else 1.0)
    total = sum(raw.values())
    return {k: v / total for k, v in raw.items()} if total > 0 else {}


def why_text(state: ConcernState) -> str:
    score = f"{state.raw_score:.0f}/100" if state.raw_score is not None else None
    if state.band == "priority":
        text = f"One of the most visible concerns in this result ({score}, higher is better)."
    elif state.band == "watch" and score:
        text = f"Worth some attention ({score}, higher is better)."
    elif state.band == "watch":
        text = "Not measured, but you told us it matters to you."
    elif state.band == "good":
        text = f"Looking good ({score}). No need to target it."
    else:
        text = "Not measured in this result."
    if state.self_reported and state.raw_score is not None:
        text += " You told us this matters to you, so it gets extra weight."
    return text
