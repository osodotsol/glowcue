---
name: backend-engineering
description: Procedures for building the GlowCue FastAPI backend. Covers adding an endpoint, Pydantic schemas, configuration, error envelopes, services vs routes vs engine separation, logging, and backend tests. Use when creating or changing anything under backend/ that is not YouCam-specific (use youcam-integration for that) or recommendation logic (use recommendation-engine).
paths: "backend/**"
---

# Backend Engineering

Rules: `.claude/rules/backend.md` (auto-loaded). Contracts: `docs/API_CONTRACTS.md`, `docs/DATA_MODEL.md`.

## Prerequisites
`backend/.venv` exists. Create it with `cd backend && python -m venv .venv && .venv/Scripts/python -m pip install -r requirements-dev.txt`.

## Procedure: add or change an endpoint
1. **Contract first:** edit `docs/API_CONTRACTS.md` (method, path, request, response, errors) and the models in `app/models.py`.
2. **Test first:** add `backend/tests/test_<route>.py` using `fastapi.testclient.TestClient(app)` with success, validation error (422) and domain error (envelope) cases.
3. **Service or engine:** put logic in `app/services/` (I/O) or `app/engine/` (pure). Keep the route thin.
4. **Route:** add it to `app/routes/<area>.py` and include the router in `app/main.py` with the `/api` prefix.
5. **Mirror the types** in `frontend/src/lib/types.ts` if the frontend consumes it.
6. **Verify:** run pytest, then `ruff check` and `ruff format --check`.

## Procedure: add a configuration value
Add a typed field with a safe default to `Settings` in `app/config.py`. Document it in the env table in `docs/DEPLOYMENT.md`. Add it to `backend/.env.example` **only** if the owner must set it locally. Secrets have no default.

## Error handling pattern
- Raise `AppError(code, message, status, retryable)`. One exception handler renders the envelope.
- Validation errors stay FastAPI's 422, but the frontend maps them to friendly copy.

## Quality checks
- [ ] No business logic in routes. No I/O in `engine/`.
- [ ] Every new code path has a test. pytest and ruff are green.
- [ ] Contracts and types are updated together.
- [ ] Logs carry no image bytes or keys.

## Output and completion
A working endpoint with tests and docs. Check it at `/docs` (Swagger) in mock mode.
