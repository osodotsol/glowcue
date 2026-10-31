---
paths:
  - "backend/tests/**"
  - "backend/app/engine/**"
  - "scripts/tests/**"
  - "frontend/src/**/*.test.ts"
  - "frontend/src/**/*.test.tsx"
  - "frontend/e2e/**"
---
# Testing rules

- **Test with every change:** every engine rule, normaliser mapping, validator and route gets at least one test. Fix bugs test-first: write the failing test, then the fix.
- **Never call the network in tests.** Mock YouCam with `httpx.MockTransport`. Fixtures come from the sanitised recorded response in `backend/app/fixtures/`.
- **Name tests after behaviour:** `test_<unit>_<behaviour>`, for example `test_optimiser_respects_budget`.
- **Cover the edge cases** in `docs/RECOMMENDATION_ENGINE.md` §9.4 and the failure scenarios in `docs/TEST_PLAN.md`.
- **Coverage target:** `backend/app/engine/` ≥ 90 % (`pytest --cov=app/engine`). Other modules should have meaningful coverage, not a number chased for its own sake.
- **E2E:** one Playwright smoke test in mock mode, covering landing → sample → results → routine → cart → checkout.
- **Reporting:** paste real counts from command output (e.g. "42 passed in 1.8s") into completion reports and `docs/PROJECT_STATUS.md`. Never write "all tests pass" without the output.
