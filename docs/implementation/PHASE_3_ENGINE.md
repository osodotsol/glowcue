# Phase 3: Catalogue, recommendation engine and routine builder

**Objective:** a deterministic, explainable, budget-aware recommendation engine with AM/PM routines, behind `POST /api/recommendations`.
**Prompts:** [05-product-catalogue](../prompts/05-product-catalogue.md), [06-recommendation-engine](../prompts/06-recommendation-engine.md), [07-routine-builder](../prompts/07-routine-builder.md) · **Branch:** `feat/recommendation-engine` · **Depends on:** Phase 1 (models), and preferably Phase 2 (real fixture) · **Skill:** `/recommendation-engine`

## Acceptance checks
- [ ] 15 validated catalogue products. Banned-word and no-bleach tests pass.
- [ ] Engine invariants 1–9 (see the skill) each have tests. Engine coverage ≥ 90%.
- [ ] All [§9.4 edge cases](../RECOMMENDATION_ENGINE.md) tested.
- [ ] Response time < 300 ms for the full catalogue.
- [ ] Golden example (sample fixture, default prefs) reviewed by the owner in the completion report.

## Fallback if behind schedule
Skip alternatives (swap) and keep the core optimiser plus routine.
