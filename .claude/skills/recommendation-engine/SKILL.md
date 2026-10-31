---
name: recommendation-engine
description: Builds and changes GlowCue's deterministic recommendation engine. Covers metric semantics (raw_score, higher means healthier), priority bands, hard filters, the exhaustive budget/coverage optimiser, AM/PM routine rules, receipts (explanations), alternatives, and the catalogue and cosmetic-claim rules. Use for any work in backend/app/engine/, backend/app/data/catalogue.json, or questions about why a product was or wasn't recommended.
paths: "backend/app/engine/**, backend/app/data/**"
---

# Recommendation Engine

Specification: `docs/RECOMMENDATION_ENGINE.md` (§9.1 catalogue, §9.2 logic, §9.3 pseudocode, §9.4 edge cases). The spec is authoritative. When logic changes, change the spec in the same commit.

## Invariants (tests must enforce these)
1. **Semantics:** severity = 100 − `raw_score`. Never use `ui_score` for ranking.
2. **Determinism:** the same input always gives the same output. Tie-break by lower cost, then fewer products, then product id.
3. **Hard filters before scoring:** owned categories, fragrance-free, sensitive or redness priority (exclude non-`sensitive_ok`).
4. **Slots:** at most 1 cleanser, moisturiser and sunscreen (each required unless owned); at most 2 serums, 1 eye product and 1 exfoliant; total at most the routine-size limit; cost at most the budget.
5. **Coverage:** Σ wᶜ × min(1, Σ target). The per-concern cap removes redundancy.
6. **Routine rules:**
   - SPF goes last in AM and never in PM;
   - vitamin C is AM only;
   - retinoids and AHA/BHA exfoliants are PM only and never on the same night;
   - exfoliants are used 2–3× a week.
7. **Receipts:** every selected product has at least one receipt quoting the real metric value and the ingredient. Sunscreen gets the protective receipt.
8. **Infeasible budget:** return the cheapest valid core with `budget_status: "over"`, the amount over, and suggestions. Never return an empty routine silently.
9. **Claims:** catalogue and copy use cosmetic phrasing. Banned words: treat, cure, heal, acne vulgaris, rosacea, melasma, eczema, whitening, bleach, hydroquinone, mercury, prescription.

## Procedure: change a rule
1. Update the spec section and write or adjust the failing test (`backend/tests/test_engine_*.py`).
2. Implement in the right module:
   - `concerns.py`: bands and weights;
   - `scoring.py`: coverage;
   - `optimiser.py`: enumeration;
   - `routine.py`: ordering and conflicts;
   - `explain.py`: receipts.
3. Run the engine tests with coverage: `cd backend && .venv/Scripts/python -m pytest tests -q -k engine --cov=app/engine --cov-report=term-missing`. The target is at least 90%.
4. Run the **golden example** (the sample fixture with default preferences). Paste the selected products, coverage and total into the completion report so the owner can sanity-check it.

## Procedure: change the catalogue
Edit `data/catalogue.json`. The loader's validator checks:
- unique ids;
- valid enums;
- targets between 0 and 1;
- prices above 0;
- banned words;
- `brand == "GlowCue Demo"`;
- `source == "fictional_demo"`.

Then re-run the engine tests and the golden example.

## Output and completion
Spec, tests and implementation stay in sync. Coverage is at least 90%. The golden example is reviewed.
