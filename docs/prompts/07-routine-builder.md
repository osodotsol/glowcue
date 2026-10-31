# 07: Morning and evening routine builder

**Branch:** `feat/recommendation-engine` · **Phase:** 3 · **Skill:** `/recommendation-engine` · **Depends on:** 06

## Objective
Turn the selected products into ordered AM and PM routines with frequencies and conflict-safe scheduling, included in `RecommendationResult.routine`.

## Context
`docs/RECOMMENDATION_ENGINE.md` §9.2 step 8, the skill's invariant 6, `docs/DATA_MODEL.md` (`Step`).

## Instructions
1. `engine/routine.py: build_routine(selected, owned) -> Routine`.
   - AM order: cleanser → vitamin C, niacinamide or hydrating serum → eye → moisturiser → **sunscreen last**.
   - PM order: cleanser → exfoliant or retinol → hydrating or calming serum → eye → moisturiser.
2. Placement rules:
   - vitamin C AM only;
   - retinol and AHA PM only;
   - both selected → retinol on nights 1, 3 and 5 and the exfoliant on nights 2 and 4, with the note "start retinol 2×/week" and `frequency` set accordingly;
   - SPF never in PM.
3. Owned categories appear as placeholder steps ("Your own cleanser") so the routine reads as complete.
4. Each step's `instruction` comes from the product's `usage`, with plain-English notes.

## Expected files
`backend/app/engine/routine.py`, `backend/tests/test_engine_routine.py`, integration into `engine/__init__.py`.

## Constraints
Pure and deterministic. No medical language.

## Acceptance criteria
Every rule above has a test. The sample golden example produces a sensible AM/PM routine, pasted into the report.

## Required tests
SPF last in AM and absent from PM; vitamin C not in PM; retinol and AHA not on the same night; owned placeholders; minimal routine (3 products); maximal routine (7).

## Definition of completion
Tests green. The engine phase gate (PHASE_3) is fully checked. PR via prompt 19.
