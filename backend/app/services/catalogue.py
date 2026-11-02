"""Loads and validates data/catalogue.json once. Any problem fails fast at startup."""

from __future__ import annotations

import json
import re
from functools import lru_cache
from pathlib import Path

from app.models import Catalogue, Product

CATALOGUE_PATH = Path(__file__).resolve().parent.parent / "data" / "catalogue.json"

# Cosmetic-claims policy (docs/RECOMMENDATION_ENGINE.md 9.1) and the "no-bleach promise" (ADR-003).
BANNED_TERMS = re.compile(
    r"\b(treat(s|ed|ing|ment)?|cures?|cured|heal(s|ed|ing)?|acne vulgaris|rosacea|melasma|eczema|whiten\w*|"
    r"bleach\w*|hydroquinone|mercury|prescription|steroids?|diagnos\w*)\b",
    re.I,
)


class CatalogueError(ValueError):
    pass


def banned_terms_in(text: str) -> list[str]:
    return sorted({m.group(0).lower() for m in BANNED_TERMS.finditer(text)})


def parse_catalogue(raw: dict) -> Catalogue:
    catalogue = Catalogue.model_validate(raw)
    ids = [p.id for p in catalogue.products]
    duplicates = sorted({i for i in ids if ids.count(i) > 1})
    if duplicates:
        raise CatalogueError(f"duplicate product ids: {duplicates}")
    for product in catalogue.products:
        found = banned_terms_in(product.model_dump_json())
        if found:
            raise CatalogueError(f"{product.id} uses non-cosmetic or banned wording: {found}")
    for category in ("cleanser", "moisturiser", "sunscreen"):
        if not any(p.category == category and p.sensitive_ok for p in catalogue.products):
            raise CatalogueError(f"the catalogue needs at least one sensitive-friendly {category}")
    return catalogue


@lru_cache
def get_catalogue() -> Catalogue:
    return parse_catalogue(json.loads(CATALOGUE_PATH.read_text(encoding="utf-8")))


def products_by_id() -> dict[str, Product]:
    return {p.id: p for p in get_catalogue().products}
