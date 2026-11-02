"""Pydantic schemas for every HTTP boundary. Mirrors docs/DATA_MODEL.md and frontend/src/lib/types.ts."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

# The nine scored attributes GlowCue uses from YouCam AI Skin Analysis v2.1 SD (docs/YOUCAM_API.md 6.3).
# `dark_circles` is GlowCue's name for YouCam's `dark_circle_v2`.
ConcernKey = Literal[
    "oiliness", "moisture", "texture", "pore", "acne", "redness", "age_spot", "wrinkle", "dark_circles"
]  # fmt: skip
CONCERN_KEYS: tuple[str, ...] = ConcernKey.__args__  # type: ignore[attr-defined]
CONCERN_LABELS: dict[str, str] = {
    "oiliness": "Shine & oiliness",
    "moisture": "Hydration",
    "texture": "Texture",
    "pore": "Pores",
    "acne": "Blemishes",
    "redness": "Redness",
    "age_spot": "Dark spots",
    "wrinkle": "Fine lines",
    "dark_circles": "Under-eye circles",
}

Band = Literal["priority", "watch", "good", "not_measured"]
SkinType = Literal["normal", "oily", "dry", "combination"]
Category = Literal["cleanser", "toner_exfoliant", "serum", "eye", "moisturiser", "sunscreen"]
CATEGORIES: tuple[str, ...] = Category.__args__  # type: ignore[attr-defined]
TimeOfDay = Literal["am", "pm"]
Frequency = Literal["daily", "2-3x weekly"]
RoutineSize = Literal["minimal", "balanced", "complete"]
AnalysisMode = Literal["demo", "live"]


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


# ----------------------------------------------------------------------------- analysis
class Metric(StrictModel):
    key: ConcernKey
    label: str
    raw_score: float | None = Field(default=None, ge=1, le=100)  # higher = healthier-looking (YouCam [V])
    ui_score: int | None = Field(default=None, ge=1, le=100)
    band: Band = "not_measured"


class NormalizedAnalysis(StrictModel):
    analysis_id: str
    mode: AnalysisMode
    provider: str  # human-readable source; for demo data this says so explicitly
    is_demo: bool
    profile_id: str | None = None
    metrics: list[Metric]
    skin_type: SkinType | None = None
    notice: str


class DemoProfile(StrictModel):
    id: str
    name: str
    summary: str


class DemoAnalysisRequest(StrictModel):
    profile_id: str = Field(min_length=1, max_length=40)


# ----------------------------------------------------------------------------- catalogue
class Product(StrictModel):
    id: str = Field(pattern=r"^gc-[a-z]+-\d{2}$")
    name: str
    brand: Literal["GlowCue Demo"]
    category: Category
    description: str
    key_ingredients: list[str] = Field(min_length=1)
    ingredients_inci: str
    targets: dict[ConcernKey, float]
    skin_types: list[SkinType] = Field(min_length=1)
    time_of_day: list[TimeOfDay] = Field(min_length=1)
    frequency: Frequency
    usage: str
    actives: list[str] = []
    fragrance_free: bool
    sensitive_ok: bool
    cautions: list[str] = []
    price: int = Field(gt=0)
    currency: Literal["NGN"]
    pack: Literal["pump", "tube", "dropper", "jar", "bottle"]  # drawn as a generic SVG packshot by the frontend
    source: Literal["fictional_demo"]

    @field_validator("targets")
    @classmethod
    def _targets_in_range(cls, v: dict[str, float]) -> dict[str, float]:
        if any(not 0 < s <= 1 for s in v.values()):
            raise ValueError("target strengths must be in (0, 1]")
        return v


class Catalogue(StrictModel):
    disclaimer: str
    currency: Literal["NGN"]
    products: list[Product]


# ----------------------------------------------------------------------------- recommendations
class MetricInput(StrictModel):
    key: ConcernKey
    raw_score: float | None = Field(default=None, ge=1, le=100)


class Preferences(StrictModel):
    budget: int = Field(ge=1000, le=1_000_000)
    owned: list[Category] = []
    concerns: list[ConcernKey] = Field(default=[], max_length=9)  # what the customer told us matters to them
    skin_type: SkinType | None = None  # self-reported; overrides the analysis when given
    fragrance_free: bool = False
    sensitive: bool = False
    routine_size: RoutineSize = "balanced"
    pinned: list[str] = Field(default=[], max_length=6)  # product ids the customer swapped in


class RecommendationRequest(StrictModel):
    metrics: list[MetricInput] = Field(min_length=1, max_length=9)
    skin_type: SkinType | None = None
    preferences: Preferences

    @field_validator("metrics")
    @classmethod
    def _unique_keys(cls, v: list[MetricInput]) -> list[MetricInput]:
        if len({m.key for m in v}) != len(v):
            raise ValueError("each metric key may appear only once")
        return v


class Priority(StrictModel):
    key: ConcernKey
    label: str
    band: Band
    raw_score: float | None
    self_reported: bool
    why_text: str


class Receipt(StrictModel):
    concern_key: ConcernKey | None  # None for the sunscreen "protects every step" receipt
    metric_raw_score: float | None
    ingredient: str
    claim_text: str


class Alternative(StrictModel):
    product_id: str
    price_delta: int
    coverage_pct: float
    within_budget: bool


class SelectedProduct(StrictModel):
    product_id: str
    slot: Category
    receipts: list[Receipt]
    alternatives: list[Alternative]


class Step(StrictModel):
    order: int
    product_id: str
    instruction: str
    frequency: Frequency
    note: str | None = None


class Routine(StrictModel):
    am: list[Step]
    pm: list[Step]


class RecommendationResult(StrictModel):
    mode: Literal["targeted", "maintenance"]
    priorities: list[Priority]
    selected: list[SelectedProduct]
    routine: Routine
    coverage_pct: float
    total: int
    budget: int
    currency: Literal["NGN"]
    budget_status: Literal["within", "over"]
    over_by: int
    warnings: list[str]
    skipped_owned: list[Category]
    excluded: list[str]  # human-readable notes on products filtered out by preferences
    unaddressed: list[ConcernKey]


# ----------------------------------------------------------------------------- cart
class CartItem(StrictModel):
    product_id: str = Field(min_length=1, max_length=40)
    qty: int = Field(ge=1, le=10)


class CartQuoteRequest(StrictModel):
    items: list[CartItem] = Field(max_length=30)


class CartLine(StrictModel):
    product_id: str
    name: str
    qty: int
    unit_price: int
    line_total: int


class CartQuote(StrictModel):
    lines: list[CartLine]
    subtotal: int
    currency: Literal["NGN"]
    item_count: int
    notice: str


# ----------------------------------------------------------------------------- config / errors
class PublicConfig(StrictModel):
    mode: AnalysisMode
    live_enabled: bool
    currency: Literal["NGN"]
    budget_default: int
    budget_min: int
    budget_max: int
    disclaimer: str


class ErrorDetail(StrictModel):
    code: str
    message: str
    retryable: bool = False
    retake: bool = False  # True when another photo (better light, framing, angle) is likely to fix it


class ErrorBody(StrictModel):
    error: ErrorDetail


# ----------------------------------------------------------------------------- live analysis jobs
AnalysisStatus = Literal["running", "success", "error"]


class AnalysisJob(StrictModel):
    """State of a live analysis: running, then a NormalizedAnalysis on success or an ErrorDetail on error."""

    analysis_id: str
    status: AnalysisStatus
    analysis: NormalizedAnalysis | None = None
    error: ErrorDetail | None = None
