# 16: Testing and debugging pass

**Branch:** `test/end-to-end` · **Phase:** 5 · **Skill:** `/test-and-verify` · **Reviewer:** `qa-engineer` · **Depends on:** 15

## Objective
Close coverage gaps, run every failure scenario, fix defects, and leave a recorded, green test matrix.

## Context
`docs/TEST_PLAN.md`, `.claude/rules/testing.md`, `docs/RECOMMENDATION_ENGINE.md` §9.4, `docs/PRD.md` §5.5 (error scenarios).

## Instructions
1. Delegate to `qa-engineer` for a traceability table (every PRD acceptance criterion → test) and a list of gaps.
2. Add the missing tests. The engine must reach ≥ 90% (`--cov=app/engine --cov-report=term-missing`).
3. Run the failure-scenario matrix:

   | Area | Scenarios |
   |---|---|
   | Upload | GIF, 11 MB, 300 px, no consent |
   | YouCam (mocked) | face too small, dark, no face, NSFW, credit insufficiency, 401, 429, 500, timeout |
   | Limits | kill switch, per-IP cap, global cap, credit floor |
   | Engine | budget below core, all owned, all good, missing metrics |
   | UI | refresh mid-flow, back button, offline |

   Record each with its result.
4. Fix defects test-first. Keep each fix small and committed separately (`fix: …`).
5. Run `/test-and-verify all`, then paste the summary lines into PROJECT_STATUS.

## Expected files
New or updated tests in `backend/tests/`, `frontend/src/**/*.test.ts` and `frontend/e2e/`; minimal fixes; `docs/TEST_PLAN.md` (results table).

## Constraints
No live calls. Don't weaken assertions to make tests pass.

## Acceptance criteria
Matrix 100% executed. Zero failing tests. Engine coverage ≥ 90%. `qa-engineer` verdict PASS or PASS WITH GAPS, with the gaps accepted by the owner.

## Required tests
Everything above.

## Definition of completion
Results table in `docs/TEST_PLAN.md`. Report. PR via prompt 19.
