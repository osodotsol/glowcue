"""Receipts: why each product was chosen, quoting the real score and ingredient (spec 9.2 step 9)."""

from __future__ import annotations

from app.engine.concerns import ConcernState
from app.models import Product, Receipt

CLAIMS = {
    "oiliness": "helps balance the look of shine",
    "moisture": "helps skin look and feel hydrated",
    "texture": "helps smooth the look of uneven texture",
    "pore": "helps refine the look of pores",
    "acne": "helps keep the look of blemishes in check",
    "redness": "helps calm the look of redness",
    "age_spot": "helps even the look of dark spots",
    "wrinkle": "helps soften the look of fine lines",
    "dark_circles": "helps brighten the look of under-eye circles",
}
SPF_CLAIM = "Daily SPF protects the results of every other step."


def receipts_for(product: Product, weights: dict[str, float], states: dict[str, ConcernState]) -> list[Receipt]:
    ingredient = ", ".join(product.key_ingredients[:2])
    out: list[Receipt] = []
    covered = sorted(
        (c for c in weights if product.targets.get(c, 0) > 0), key=lambda c: (-weights[c] * product.targets[c], c)
    )
    for concern in covered:
        state = states[concern]
        if state.raw_score is not None:
            lead = f"Your {state.label.lower()} scored {state.raw_score:.0f}/100 (higher is better)"
        else:
            lead = f"You told us {state.label.lower()} matters to you"
        out.append(
            Receipt(
                concern_key=concern,
                metric_raw_score=state.raw_score,
                ingredient=ingredient,
                claim_text=f"{lead} → {ingredient} → {CLAIMS[concern]}.",
            )
        )
    if product.category == "sunscreen":
        out.append(Receipt(concern_key=None, metric_raw_score=None, ingredient=ingredient, claim_text=SPF_CLAIM))
    if not out:  # a core step that targets nothing active (e.g. maintenance routines)
        out.append(
            Receipt(
                concern_key=None,
                metric_raw_score=None,
                ingredient=ingredient,
                claim_text=f"An essential daily {product.category} step with {ingredient}.",
            )
        )
    return out
