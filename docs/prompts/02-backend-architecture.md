# 02: Backend architecture (mock-mode API surface)

**Branch:** `feat/backend-api` · **Phase:** 1 · **Skill:** `/backend-engineering` · **Depends on:** 01

## Objective
Implement the full GlowCue API surface from `docs/API_CONTRACTS.md` in **mock mode**: configuration, Pydantic models, error envelope, limits, results store, and analysis endpoints backed by a provisional fixture.

## Context
`docs/API_CONTRACTS.md`, `docs/DATA_MODEL.md`, `docs/ARCHITECTURE.md` §7.2, `docs/PRD.md` §5.5–5.6, `docs/SECURITY_PRIVACY.md` §5.

## Instructions
1. Extend `app/config.py` with:
   - `YOUCAM_MODE` (`mock` | `live`, default `mock`)
   - `YOUCAM_API_KEY` (optional `SecretStr`; required when live)
   - `LIVE_ANALYSIS_ENABLED`, `MAX_LIVE_PER_DAY=25`, `PER_IP_PER_DAY=5`, `CREDIT_FLOOR=100`
   - `FRONTEND_ORIGIN`, `CURRENCY="NGN"`, `BUDGET_DEFAULT=30000`, `RESULT_TTL_SECONDS=1800`
   **Security requirements B1, B4 and B6 (from the PR #1 review; see `docs/SECURITY_PRIVACY.md` §4.4):**
   - **B1:** make `backend/.env` the authority for `YOUCAM_MODE` and `LIVE_ANALYSIS_ENABLED` by customising the settings sources so dotenv values override process environment variables. Production has no `.env`, so Render's variables apply there.
   - **B4:** log the effective mode, `live_analysis_enabled` and whether a key is present at startup, never the key.
   - **B6:** `LIVE_ANALYSIS_ENABLED` defaults to `false`; the sample endpoint never calls YouCam.
   - Tests: a `.env` value beats a conflicting environment variable (use a temporary env file, never the real one); defaults are mock and disabled.
2. `app/models.py`: every model in DATA_MODEL (`Metric`, `NormalizedAnalysis`, `Preferences`, `Product`, `RecommendationResult`, `Receipt`, `Step`, cart models, `ErrorBody`).
3. `app/errors.py`: an `AppError` exception plus a handler rendering `{"error": {code, message, retryable}}`.
4. `services/results_store.py` (cachetools TTLCache, single process) and `services/limits.py` (per-IP and global daily counters, kill switch; the credit-floor hook comes later in prompt 03).
5. `services/image_validation.py`: consent first, ≤ 10 MB, JPEG/PNG by magic bytes, short side ≥ 480 px, Pillow re-encode to JPEG (drops metadata), all in memory.
6. Routes:
   - `GET /api/config`
   - `POST /api/analyses` (multipart `image` + `consent`), which in mock mode stores the provisional fixture as "running" and flips to success after 3 s
   - `GET /api/analyses/{id}`
   - `GET /api/sample-analysis`
   - `GET /api/catalogue` (501 until prompt 05)
   - `POST /api/recommendations` (501 until prompt 06)
   - `POST /api/cart/quote` (501 until prompt 05)
7. Provisional fixture `app/fixtures/provisional_sample.json`, built from the **documented** SD sample in `docs/YOUCAM_API.md` and clearly marked `"provisional": true`. It's replaced in prompt 04.
8. Mirror the types in `frontend/src/lib/types.ts`.

## Expected files
`backend/app/{config.py,models.py,errors.py,main.py}`, `backend/app/routes/*.py`, `backend/app/services/{results_store.py,limits.py,image_validation.py}`, `backend/app/fixtures/provisional_sample.json`, `backend/tests/test_*.py`, `frontend/src/lib/types.ts`, `docs/API_CONTRACTS.md` (if refined).

## Constraints
No network calls. No disk writes of images. Single worker. Keep routes thin.

## Acceptance criteria
- In mock mode, `POST` then poll returns `success` with a `NormalizedAnalysis` within 5 s.
- Missing consent → 422 or 400 envelope. GIF → rejected. 300 px image → rejected. 11 MB → rejected.
- CORS headers present only for `FRONTEND_ORIGIN` and localhost.
- `/docs` lists every endpoint.

## Required tests
Route tests for every endpoint, plus validation tests (synthetic images made with Pillow in the test), the limits counter, TTL expiry (with an injectable clock) and the CORS allow/deny cases.

## Definition of completion
pytest and ruff green. Contracts and types in sync. Completion report. PR via prompt 19.
