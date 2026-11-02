from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.main import create_app


@pytest.fixture
def client() -> TestClient:
    return TestClient(create_app())


def demo_metrics(client: TestClient, profile: str = "shine-prone") -> dict:
    analysis = client.post("/api/analyses/demo", json={"profile_id": profile}).json()
    return {
        "metrics": [{"key": m["key"], "raw_score": m["raw_score"]} for m in analysis["metrics"]],
        "skin_type": analysis["skin_type"],
    }


def test_config_reports_demo_mode_and_budget_range(client):
    body = client.get("/api/config").json()
    assert body["mode"] == "demo" and body["live_enabled"] is False
    assert body["budget_min"] <= body["budget_default"] <= body["budget_max"]
    assert "not medical advice" in body["disclaimer"]


def test_demo_profiles_and_analysis_are_labelled_as_demo(client):
    profiles = client.get("/api/demo-profiles").json()
    assert {p["id"] for p in profiles} >= {"shine-prone", "dry-sensitive", "uneven-tone", "balanced"}
    body = client.post("/api/analyses/demo", json={"profile_id": "dry-sensitive"}).json()
    assert body["is_demo"] is True and body["mode"] == "demo"
    assert "not from an analysis of your photo" in body["notice"]


def test_demo_analysis_rejects_unknown_profile_with_the_error_envelope(client):
    resp = client.post("/api/analyses/demo", json={"profile_id": "nope"})
    assert resp.status_code == 404
    assert resp.json()["error"]["code"] == "unknown_profile"


def test_demo_analysis_endpoint_accepts_no_image_field(client):
    resp = client.post("/api/analyses/demo", json={"profile_id": "balanced", "image": "data:image/png;base64,AAAA"})
    assert resp.status_code == 422  # extra fields are forbidden: photos are never sent in demo mode
    assert resp.json()["error"]["code"] == "invalid_input"


def test_catalogue_lists_demo_products_with_disclaimer(client):
    body = client.get("/api/catalogue").json()
    assert len(body["products"]) == 15
    assert "fictional" in body["disclaimer"].lower()


def test_recommendations_round_trip(client):
    payload = {**demo_metrics(client), "preferences": {"budget": 30000, "concerns": ["pore"]}}
    resp = client.post("/api/recommendations", json=payload)
    assert resp.status_code == 200
    body = resp.json()
    assert body["budget_status"] == "within" and body["total"] <= 30000
    assert body["routine"]["am"][-1]["product_id"].startswith("gc-spf")


@pytest.mark.parametrize(
    "patch",
    [
        {"preferences": {"budget": 10}},  # below minimum
        {"preferences": {"budget": 30000, "owned": ["lipstick"]}},
        {"preferences": {"budget": 30000, "concerns": ["acne vulgaris"]}},
        {"preferences": {"budget": 30000, "routine_size": "huge"}},
        {"metrics": [{"key": "oiliness", "raw_score": 150}]},
        {"metrics": [{"key": "oiliness", "raw_score": 40}, {"key": "oiliness", "raw_score": 50}]},
        {"metrics": []},
    ],
)
def test_recommendations_validate_input(client, patch):
    payload = {"metrics": [{"key": "oiliness", "raw_score": 40}], "preferences": {"budget": 30000}, **patch}
    resp = client.post("/api/recommendations", json=payload)
    assert resp.status_code == 422
    assert resp.json()["error"]["code"] == "invalid_input"


def test_recommendations_reject_unknown_pinned_product(client):
    payload = {**demo_metrics(client), "preferences": {"budget": 30000, "pinned": ["gc-xxx-99"]}}
    resp = client.post("/api/recommendations", json=payload)
    assert resp.status_code == 422 and resp.json()["error"]["code"] == "unknown_product"


def test_cart_quote_uses_catalogue_prices_and_merges_lines(client):
    resp = client.post(
        "/api/cart/quote",
        json={"items": [{"product_id": "gc-cln-01", "qty": 2}, {"product_id": "gc-cln-01", "qty": 1}]},
    )
    body = resp.json()
    assert resp.status_code == 200
    assert body["lines"] == [
        {"product_id": "gc-cln-01", "name": "Gentle Cream Cleanser", "qty": 3, "unit_price": 5500, "line_total": 16500}
    ]
    assert body["subtotal"] == 16500 and body["item_count"] == 3
    assert "no payment" in body["notice"]


def test_cart_quote_ignores_client_prices(client):
    resp = client.post("/api/cart/quote", json={"items": [{"product_id": "gc-cln-01", "qty": 1, "price": 1}]})
    assert resp.status_code == 422  # unknown fields (like a client price) are rejected outright


@pytest.mark.parametrize(
    "items",
    [
        [{"product_id": "gc-xxx-99", "qty": 1}],
        [{"product_id": "gc-cln-01", "qty": 0}],
        [{"product_id": "gc-cln-01", "qty": 11}],
    ],
)
def test_cart_quote_validates_items(client, items):
    resp = client.post("/api/cart/quote", json={"items": items})
    assert resp.status_code == 422
    assert "error" in resp.json()


def test_empty_cart_quote_is_zero(client):
    assert client.post("/api/cart/quote", json={"items": []}).json()["subtotal"] == 0


def test_cors_allows_frontend_origin_only(client):
    ok = client.options(
        "/api/catalogue", headers={"Origin": "http://localhost:5173", "Access-Control-Request-Method": "GET"}
    )
    bad = client.options(
        "/api/catalogue", headers={"Origin": "https://evil.example", "Access-Control-Request-Method": "GET"}
    )
    assert ok.headers.get("access-control-allow-origin") == "http://localhost:5173"
    assert "access-control-allow-origin" not in bad.headers
