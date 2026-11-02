"""Top-level recommendation: scores + preferences + catalogue -> explainable routine (spec 9.3)."""

from __future__ import annotations

from app.engine.concerns import assess, weights, why_text
from app.engine.explain import receipts_for
from app.engine.optimiser import SIZE_LIMIT, best_routine, cheapest_core
from app.engine.routine import build_routine
from app.engine.scoring import concern_coverage, coverage
from app.models import (
    Alternative,
    Preferences,
    Priority,
    Product,
    RecommendationRequest,
    RecommendationResult,
    SelectedProduct,
)

_NON_SENSITIVE_REASON = "you marked sensitive skin"
_REDNESS_REASON = "redness is one of your priorities"


def _filter_pool(
    catalogue: list[Product], prefs: Preferences, gentle_reason: str | None
) -> tuple[list[Product], list[str]]:
    excluded: list[str] = []
    pool = {p.id: p for p in catalogue}.values()  # de-duplicate defensively
    pool = [p for p in pool if p.category not in prefs.owned]
    if prefs.fragrance_free:
        excluded += [f"{p.name}: contains fragrance" for p in pool if not p.fragrance_free]
        pool = [p for p in pool if p.fragrance_free]
    if gentle_reason:
        excluded += [f"{p.name}: skipped because {gentle_reason}" for p in pool if not p.sensitive_ok]
        pool = [p for p in pool if p.sensitive_ok]
    return sorted(pool, key=lambda p: p.id), excluded


def _alternatives(
    chosen: tuple[Product, ...], pool: list[Product], w: dict[str, float], total: int, budget: int
) -> dict[str, list[Alternative]]:
    out: dict[str, list[Alternative]] = {}
    chosen_ids = {p.id for p in chosen}
    norm = sum(w.values()) or 1.0
    for product in chosen:
        options = []
        for alt in pool:
            if alt.category != product.category or alt.id in chosen_ids:
                continue
            swapped = [alt if p.id == product.id else p for p in chosen]
            delta = alt.price - product.price
            options.append(
                Alternative(
                    product_id=alt.id,
                    price_delta=delta,
                    coverage_pct=round(100 * coverage(swapped, w) / norm, 1) if w else 100.0,
                    within_budget=total + delta <= budget,
                )
            )
        options.sort(key=lambda a: (not a.within_budget, -a.coverage_pct, a.price_delta, a.product_id))
        out[product.id] = options[:3]
    return out


def recommend(request: RecommendationRequest, catalogue: list[Product]) -> RecommendationResult:
    prefs = request.preferences
    states = assess(request.metrics, prefs.concerns)
    by_key = {s.key: s for s in states}
    w = weights(states)
    skin_type = prefs.skin_type or request.skin_type

    redness_priority = by_key.get("redness") is not None and by_key["redness"].band == "priority"
    gentle_reason = _NON_SENSITIVE_REASON if prefs.sensitive else (_REDNESS_REASON if redness_priority else None)
    pool, excluded = _filter_pool(catalogue, prefs, gentle_reason)
    owned, pinned = set(prefs.owned), set(prefs.pinned)

    warnings: list[str] = []
    best = best_routine(pool, w, skin_type, prefs.budget, owned, pinned, SIZE_LIMIT[prefs.routine_size])
    if best is not None:
        chosen, total, status = best.products, best.cost, "within"
    else:
        chosen = cheapest_core(pool, owned, pinned)
        total, status = sum(p.price for p in chosen), "over"
        warnings.append("Your budget is below the cheapest complete basic routine in our catalogue.")
    over_by = max(0, total - prefs.budget)

    for category in ("cleanser", "moisturiser", "sunscreen"):
        if category in owned:
            if category == "sunscreen":
                warnings.append("You already own a sunscreen: keep using it every morning as the last step.")
        elif not any(p.category == category for p in chosen):
            warnings.append(f"No {category} in our catalogue matches your filters.")

    routine, routine_notes = build_routine(chosen)
    warnings += routine_notes
    if any(a in ("retinoid", "aha", "bha", "vitc") for p in chosen for a in p.actives):
        warnings.append("Patch test new active products first.")

    alternatives = _alternatives(chosen, pool, w, total, prefs.budget)
    selected = [
        SelectedProduct(
            product_id=p.id, slot=p.category, receipts=receipts_for(p, w, by_key), alternatives=alternatives[p.id]
        )
        for p in chosen
    ]
    norm = sum(w.values())
    return RecommendationResult(
        mode="targeted" if w else "maintenance",
        priorities=[
            Priority(
                key=s.key,
                label=s.label,
                band=s.band,
                raw_score=s.raw_score,
                self_reported=s.self_reported,
                why_text=why_text(s),
            )
            for s in states
        ],
        selected=selected,
        routine=routine,
        coverage_pct=round(100 * coverage(chosen, w) / norm, 1) if norm else 100.0,
        total=total,
        budget=prefs.budget,
        currency="NGN",
        budget_status=status,
        over_by=over_by,
        warnings=warnings,
        skipped_owned=sorted(owned),
        excluded=excluded,
        unaddressed=sorted(c for c in w if concern_coverage(chosen, c) == 0),
    )
