"""Coverage scoring (spec 9.2 step 6). The per-concern min(1, ...) cap removes redundancy."""

from __future__ import annotations

from collections.abc import Iterable

from app.models import Product

FIT_BONUS = 0.02
COST_PENALTY = 0.0001


def concern_coverage(products: Iterable[Product], concern: str) -> float:
    return min(1.0, sum(p.targets.get(concern, 0.0) for p in products))


def coverage(products: Iterable[Product], weights: dict[str, float]) -> float:
    products = list(products)
    return sum(w * concern_coverage(products, c) for c, w in weights.items())


def skin_type_fit(products: Iterable[Product], skin_type: str | None) -> float:
    """Share of texture-defining products (cleanser, moisturiser) formulated for this skin type."""
    texture = [p for p in products if p.category in ("cleanser", "moisturiser")]
    if not skin_type or not texture:
        return 0.0
    return sum(skin_type in p.skin_types for p in texture) / len(texture)


def objective(products: list[Product], weights: dict[str, float], skin_type: str | None, budget: int) -> float:
    cost = sum(p.price for p in products)
    return coverage(products, weights) + FIT_BONUS * skin_type_fit(products, skin_type) - COST_PENALTY * cost / budget
