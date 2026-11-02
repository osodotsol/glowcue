# 06: Recommendation engine

**Branch:** `feat/recommendation-engine` · **Phase:** 3 · **Skill:** `/recommendation-engine` · **Depends on:** 04 (or the provisional fixture), 05

## Objective
Implement the deterministic, explainable, budget-aware engine: priorities → filters → exhaustive optimiser → receipts → alternatives, exposed at `POST /api/recommendations`.

## Context
`docs/RECOMMENDATION_ENGINE.md` §9.2–9.4 (authoritative), `.claude/skills/recommendation-engine/SKILL.md` (invariants 1–9), `docs/API_CONTRACTS.md`.

## Instructions
1. `engine/concerns.py`: severity, bands, normalised weights over priority and watch concerns, maintenance mode.
2. `engine/scoring.py`: `coverage(combo, weights)` with a per-concern cap, plus a skin-type fit bonus (+0.02).
3. `engine/optimiser.py`: enumerate subsets of the filtered pool under the slot constraints and budget. Use the key `(coverage − 0.0001·cost/budget, −len)`, then a deterministic tie-break by sorted ids. Prune early by category counts. Infeasible budget → cheapest valid core with an `over_by` amount.
4. `engine/explain.py`: receipts like "Texture scored 41/100 (higher is better) → lactic acid → helps smooth the look of uneven texture". Sunscreen gets the protective receipt.
5. `engine/alternatives.py`: up to 3 per slot, ranked by single-swap coverage within budget.
6. `engine/__init__.py: recommend(metrics, skin_type, prefs, catalogue) -> RecommendationResult`, plus the route. (Routine ordering is a placeholder until prompt 07.)

## Expected files
`backend/app/engine/*.py`, `backend/app/routes/recommendations.py`, `backend/tests/test_engine_*.py`, `docs/RECOMMENDATION_ENGINE.md` (only if logic is clarified).

## Constraints
Pure functions only, with no I/O, randomness or time. Under 300 ms. Never use `ui_score` for ranking.

## Acceptance criteria
Invariants 1–5 and 7–8 tested. Every §9.4 edge case tested. Engine coverage ≥ 90%. Golden example output included in the report.

## Required tests
Budget respected; owned categories skipped; fragrance-free and sensitive filters; redness-priority filter; no redundant duplicates (cap); determinism (run twice, equal); tie-break; infeasible budget; all-good maintenance; missing metrics; performance (< 300 ms).

## Definition of completion
Tests and coverage green. The owner reviews the golden example.
