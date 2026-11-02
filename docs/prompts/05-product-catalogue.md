# 05: Product catalogue

**Branch:** `feat/recommendation-engine` · **Phase:** 3 · **Skill:** `/recommendation-engine` · **Depends on:** 02

## Objective
Create the 15-product **GlowCue Demo** catalogue with a strict validator, the catalogue endpoint, server-side cart quoting and consistent product artwork.

## Context
`docs/RECOMMENDATION_ENGINE.md` §9.1 (schema, product table, admission policy, copy rules), `docs/decisions/ADR-003-product-catalogue.md`, `docs/DESIGN_SYSTEM.md` §8.4.

## Instructions
1. `app/data/catalogue.json` holds the 15 products from §9.1 using the exact schema.
   - Prices are in NGN and illustrative. Suggested range: ₦4,000–₦22,000, with cleanser < serum, and two budget options.
   - `ingredients_inci` is marked illustrative.
   - `brand: "GlowCue Demo"`, `source: "fictional_demo"`.
2. `app/catalogue.py` loads and validates at startup and fails fast. It checks:
   - unique ids;
   - enums for `category`, `time_of_day` and `frequency`;
   - targets in [0, 1] and keyed by known concerns;
   - price > 0;
   - required fields;
   - banned words (from the skill) absent from every text field;
   - admission policy (no hydroquinone, mercury, steroids, whitening or bleach).
3. `GET /api/catalogue` and `POST /api/cart/quote`. The quote recomputes from the catalogue, rejects unknown ids (400) and quantities outside 1–5.
4. Product artwork: 15 flat SVG packshots in `frontend/public/products/<id>.svg`, in a consistent style (bottle, tube, jar or dropper by category), labelled "GlowCue Demo" and using design tokens.

## Expected files
`backend/app/data/catalogue.json`, `backend/app/catalogue.py`, `backend/app/routes/{catalogue.py,cart.py}`, `backend/tests/test_catalogue.py`, `backend/tests/test_cart.py`, `frontend/public/products/*.svg`.

## Constraints
Cosmetic phrasing only ("helps the look of"). No real brand names or logos.

## Acceptance criteria
Validator rejects each invalid fixture variant (one test per rule). The endpoint returns 15 products. Quote totals are exact.

## Required tests
Validator rule tests, banned-word test, quote tests (sum, unknown id, quantity bounds).

## Definition of completion
Tests green. Product images render in the browser (`/products/<id>.svg`).
