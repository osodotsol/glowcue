"""Config, demo analysis, catalogue, recommendations and cart quote. Thin handlers only."""

from __future__ import annotations

from fastapi import APIRouter

from app.config import get_settings
from app.engine import recommend
from app.errors import AppError
from app.models import (
    CartLine,
    CartQuote,
    CartQuoteRequest,
    Catalogue,
    DemoAnalysisRequest,
    DemoProfile,
    NormalizedAnalysis,
    PublicConfig,
    RecommendationRequest,
    RecommendationResult,
)
from app.services.analysis import get_provider
from app.services.catalogue import get_catalogue, products_by_id
from app.services.youcam_client import live_refusal

router = APIRouter()

BUDGET_MIN, BUDGET_MAX = 5000, 150000
DISCLAIMER = (
    "GlowCue gives cosmetic skincare suggestions, not medical advice. It does not diagnose or treat any skin "
    "condition. See a dermatologist for medical concerns."
)
DEMO_STORE_NOTICE = "Demo store: products are fictional and no payment is taken."


@router.get("/config", tags=["meta"])
async def public_config() -> PublicConfig:
    settings = get_settings()
    return PublicConfig(
        mode="demo" if settings.youcam_mode == "mock" else "live",
        live_enabled=live_refusal(settings) is None,  # live mode AND the kill switch AND a key
        currency="NGN",
        budget_default=settings.budget_default,
        budget_min=BUDGET_MIN,
        budget_max=BUDGET_MAX,
        disclaimer=DISCLAIMER,
    )


@router.get("/demo-profiles", tags=["analysis"])
async def demo_profiles() -> list[DemoProfile]:
    return get_provider(get_settings()).profiles()


@router.post("/analyses/demo", tags=["analysis"])
async def demo_analysis(body: DemoAnalysisRequest) -> NormalizedAnalysis:
    """Demonstration scores for a chosen profile. Takes no photo: the selfie never leaves the browser."""
    return get_provider(get_settings()).analyse_profile(body.profile_id)


@router.get("/catalogue", tags=["catalogue"])
async def catalogue() -> Catalogue:
    return get_catalogue()


@router.post("/recommendations", tags=["recommendations"])
async def recommendations(body: RecommendationRequest) -> RecommendationResult:
    known = products_by_id()
    unknown = [pid for pid in body.preferences.pinned if pid not in known]
    if unknown:
        raise AppError("unknown_product", f"Unknown product id(s): {', '.join(unknown)}", status=422)
    return recommend(body, get_catalogue().products)


@router.post("/cart/quote", tags=["cart"])
async def cart_quote(body: CartQuoteRequest) -> CartQuote:
    """Prices always come from the catalogue, never from the client."""
    known = products_by_id()
    merged: dict[str, int] = {}
    for item in body.items:
        if item.product_id not in known:
            raise AppError("unknown_product", f"Unknown product id: {item.product_id}", status=422)
        merged[item.product_id] = min(10, merged.get(item.product_id, 0) + item.qty)
    lines = [
        CartLine(
            product_id=pid,
            name=known[pid].name,
            qty=qty,
            unit_price=known[pid].price,
            line_total=known[pid].price * qty,
        )
        for pid, qty in merged.items()
    ]
    return CartQuote(
        lines=lines,
        subtotal=sum(line.line_total for line in lines),
        currency="NGN",
        item_count=sum(line.qty for line in lines),
        notice=DEMO_STORE_NOTICE,
    )
