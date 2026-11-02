from __future__ import annotations

import copy
import json

import pytest

from app.services.catalogue import CATALOGUE_PATH, CatalogueError, banned_terms_in, get_catalogue, parse_catalogue

RAW = json.loads(CATALOGUE_PATH.read_text(encoding="utf-8"))


def test_catalogue_loads_with_fifteen_demo_products():
    catalogue = get_catalogue()
    assert len(catalogue.products) == 15
    assert all(p.brand == "GlowCue Demo" and p.source == "fictional_demo" for p in catalogue.products)
    assert "fictional" in catalogue.disclaimer.lower()


def test_catalogue_every_product_has_a_positive_ngn_price():
    assert all(p.price > 0 and p.currency == "NGN" for p in get_catalogue().products)


def test_catalogue_has_options_for_every_required_slot_including_sensitive_skin():
    products = get_catalogue().products
    for category in ("cleanser", "moisturiser", "sunscreen"):
        assert any(p.category == category and p.sensitive_ok and p.fragrance_free for p in products), category


def test_catalogue_uses_cosmetic_wording_only():
    for product in get_catalogue().products:
        assert banned_terms_in(product.model_dump_json()) == [], product.id


@pytest.mark.parametrize(
    "text", ["treats breakouts", "cures dryness", "heals skin", "a whitening serum", "skin bleaching", "rosacea"]
)
def test_banned_terms_are_detected(text):
    assert banned_terms_in(text)


def test_banned_terms_ignore_ordinary_words():
    assert banned_terms_in("healthier-looking skin, a treat for dry days") == ["treat"]  # 'treat' is still flagged
    assert banned_terms_in("helps the look of uneven tone") == []


def test_duplicate_ids_fail_fast():
    raw = copy.deepcopy(RAW)
    raw["products"].append(copy.deepcopy(raw["products"][0]))
    with pytest.raises(CatalogueError, match="duplicate"):
        parse_catalogue(raw)


def test_banned_claim_fails_fast():
    raw = copy.deepcopy(RAW)
    raw["products"][0]["description"] = "Treats dry skin."
    with pytest.raises(CatalogueError, match="banned"):
        parse_catalogue(raw)


@pytest.mark.parametrize(
    "field,value",
    [("price", 0), ("brand", "RealBrand"), ("category", "mask"), ("targets", {"oiliness": 1.5}), ("source", "real")],
)
def test_invalid_product_fields_are_rejected(field, value):
    raw = copy.deepcopy(RAW)
    raw["products"][0][field] = value
    with pytest.raises(ValueError):
        parse_catalogue(raw)
