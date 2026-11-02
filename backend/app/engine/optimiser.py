"""Exhaustive, slot-wise search for the best routine within budget (spec 9.2 steps 4-7).

Enumerating by slot (cleanser x moisturiser x sunscreen x serum pairs x eye x exfoliant) keeps the search to about a
thousand combinations for the 15-product catalogue, so it runs in milliseconds.
"""

from __future__ import annotations

import itertools
from collections.abc import Iterator
from dataclasses import dataclass

from app.engine.scoring import objective
from app.models import Product

CORE = ("cleanser", "moisturiser", "sunscreen")
SIZE_LIMIT = {"minimal": 4, "balanced": 6, "complete": 8}
MAX_SERUMS = 2


@dataclass(frozen=True)
class Choice:
    products: tuple[Product, ...]
    cost: int
    score: float


def _slot_options(pool: list[Product], category: str, required: bool, pinned: set[str]) -> list[tuple[Product, ...]]:
    items = [p for p in pool if p.category == category]
    pinned_items = [p for p in items if p.id in pinned]
    if category == "serum":
        combos = [c for n in range(MAX_SERUMS + 1) for c in itertools.combinations(items, n)]
        return [c for c in combos if all(p in c for p in pinned_items[:MAX_SERUMS])]
    if pinned_items:
        return [(pinned_items[0],)]
    if required:
        return [(p,) for p in items] or [()]  # no matching product: slot stays empty (reported as a warning)
    return [(), *((p,) for p in items)]


def enumerate_routines(pool: list[Product], owned: set[str], pinned: set[str], max_size: int) -> Iterator[tuple]:
    pool = sorted(pool, key=lambda p: p.id)
    slots = [
        _slot_options(pool, c, required=c in CORE and c not in owned, pinned=pinned)
        for c in ("cleanser", "moisturiser", "sunscreen", "serum", "eye", "toner_exfoliant")
    ]
    for parts in itertools.product(*slots):
        combo = tuple(p for part in parts for p in part)
        if len(combo) <= max_size:
            yield combo


def best_routine(
    pool: list[Product],
    weights: dict[str, float],
    skin_type: str | None,
    budget: int,
    owned: set[str],
    pinned: set[str],
    max_size: int,
) -> Choice | None:
    best: Choice | None = None
    for combo in enumerate_routines(pool, owned, pinned, max_size):
        cost = sum(p.price for p in combo)
        if cost > budget or not combo:
            continue
        score = round(objective(list(combo), weights, skin_type, budget), 9)
        # Deterministic tie-break: higher score, then lower cost, then fewer products, then first in id order.
        if best is None or (score, -cost, -len(combo)) > (best.score, -best.cost, -len(best.products)):
            best = Choice(combo, cost, score)
    return best


def cheapest_core(pool: list[Product], owned: set[str], pinned: set[str]) -> tuple[Product, ...]:
    """The cheapest complete basic routine, used when nothing fits the budget."""
    chosen: list[Product] = []
    for category in CORE:
        if category in owned:
            continue
        items = [p for p in pool if p.category == category]
        pinned_items = [p for p in items if p.id in pinned]
        if pinned_items or items:
            chosen.append(pinned_items[0] if pinned_items else min(items, key=lambda p: (p.price, p.id)))
    return tuple(chosen)
