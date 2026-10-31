# ADR-001: Technology stack

- **Status:** Accepted, 31 Oct 2026
- **Deciders:** Owner + Claude Code (CTO role)

## Context
GlowCue must be built, deployed and submitted in about 45 hours by one Python-proficient developer working mainly through Claude Code, at zero cost. It needs a secret-holding server (the YouCam key), image handling, a deterministic recommendation engine and a polished consumer web UI.

## Options considered
| Option | Pros | Cons |
|---|---|---|
| **FastAPI + React/Vite/TS + Tailwind** | Python backend matches the owner's skills. Typed contracts on both sides. Large ecosystem that AI agents know well. Free hosting. | Two deployables, so CORS needs configuring |
| Next.js full-stack (TS only) | One deployable | The owner is weaker in TS. Image handling and the engine are less natural than in Python. |
| Streamlit / Gradio | Fastest prototype | Looks like a demo, not a consumer shop. Weak for the "Design" criterion. |
| Django + templates | Batteries included | Heavier, slower to make look premium |

## Decision
- **Backend:** Python (3.14 locally, see the `.python-version` file), FastAPI, Pydantic v2, pydantic-settings, httpx, Pillow, cachetools; pytest and ruff for quality.
- **Frontend:** React + TypeScript (strict) + Vite + Tailwind CSS v4, ESLint (flat config).
- **Data:** a validated JSON catalogue. **No database.**
- **Hosting:** Render free (API) and Vercel Hobby (static SPA). See ADR-002 and `DEPLOYMENT.md`.

## Reason
Best balance of owner skill fit, agent fluency, design quality and zero cost. Typed models on both sides catch agent mistakes early.

## Consequences
- Contracts must be kept in sync across `models.py`, `API_CONTRACTS.md` and `types.ts` (enforced by review rules).
- A single Uvicorn worker, because the in-memory TTL store is per process.
- Python 3.14 is new. If a dependency lacks wheels, fall back to 3.12 everywhere and update `.python-version` and CI.
