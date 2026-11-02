---
paths:
  - "backend/**"
---
# Backend rules (FastAPI / Python)

## Structure (`backend/app/`)
- `main.py` builds the app: CORS, routers, exception handlers. It contains no business logic.
- `config.py` holds `Settings` (pydantic-settings). It's the only place env vars are read.
- `models.py` holds the Pydantic v2 request and response schemas, which mirror `docs/API_CONTRACTS.md` and `docs/DATA_MODEL.md`.
- `routes/*.py` contain thin handlers: validate, call a service or engine, return a model.
- `services/*.py` handle I/O: the YouCam client, image validation, results store and limits.
- `engine/*.py` holds pure recommendation logic, with no FastAPI, I/O or globals.
- `data/catalogue.json` is validated at startup and fails fast on errors.

## Standards
- Type hints everywhere. Use Pydantic models at every HTTP boundary and `Literal` or `Enum` for closed sets (concern keys, bands, categories).
- Use `async def` routes and `httpx.AsyncClient` with explicit timeouts (connect 10 s, read 30 s). Never use `requests` in app code.
- Errors use one envelope: `{"error": {"code": str, "message": str, "retryable": bool}}`. Map YouCam error codes to friendly codes in one table in `services/youcam_errors.py`.
- Log with the `logging` module through module loggers. Log IDs and statuses, never images, keys or full YouCam payloads.
- Run one Uvicorn worker. The in-memory TTL store assumes a single process (documented in `docs/ARCHITECTURE.md`).
- When you add or change an endpoint, update `docs/API_CONTRACTS.md` and `frontend/src/lib/types.ts` in the same change.

## Commands
```bash
cd backend && .venv/Scripts/python -m pytest -q
cd backend && .venv/Scripts/python -m ruff check . && .venv/Scripts/python -m ruff format --check .
cd backend && .venv/Scripts/python -m uvicorn app.main:app --reload --port 8000
```
