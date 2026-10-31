# 15: Frontend/backend integration (mock → live)

**Branch:** `feat/integration` · **Phase:** 5 · **Skills:** `/test-and-verify`, `/youcam-integration` · **Depends on:** 02–14

## Objective
Prove the whole journey end to end: first in mock mode, then with **one owner-approved live analysis** of a real selfie through to checkout. Fix integration defects.

## Context
`docs/API_CONTRACTS.md`, `docs/implementation/PHASE_5_INTEGRATION_QA.md`, `docs/TEST_PLAN.md`, `docs/YOUCAM_API.md` §6.8.

## Instructions
1. Run the backend (mock) and frontend (`VITE_API_BASE_URL=http://localhost:8000`). Walk the full journey and fix contract mismatches, keeping `types.ts`, `models.py` and `API_CONTRACTS.md` in sync.
2. Error paths through mocks: face too small, dark lighting, no face, credit insufficiency, 429, timeout. Each must show the right UI.
3. Add Playwright (ask before installing; then `npx playwright install chromium`) and `frontend/e2e/smoke.spec.ts` in mock mode: landing → sample → results (heatmap visible) → routine (change budget) → add to cart → checkout → clear data.
4. **Live run:**
   - ask the owner: "Approve 1 live analysis (~14 units) with your selfie?";
   - after a yes, the owner sets `YOUCAM_MODE=live` in `backend/.env` (or you run `GLOWCUE_LIVE_APPROVED=1 YOUCAM_MODE=live …`);
   - upload through the UI and complete the journey;
   - record the units delta and duration;
   - switch back to mock.
5. Test with 3 deliberately bad images (tiny, dark, no face). The tiny one is caught client-side; the others are mocked unless the owner approves more live runs.

## Expected files
`frontend/e2e/smoke.spec.ts`, `frontend/playwright.config.ts`, `frontend/package.json`, bug fixes across front and back end.

## Constraints
At most 2 live runs, each approved. Never commit the selfie.

## Acceptance criteria
The e2e smoke test is green. The live journey reached checkout with no console errors. Every error state was verified.

## Required tests
Playwright smoke, plus the full `/test-and-verify all`.

## Definition of completion
Report including units spent. PROJECT_STATUS updated. PR via prompt 19.
