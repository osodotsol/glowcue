# GlowCue — Shared Agent Conventions

> Read by **Claude Code** (imported from `CLAUDE.md`) and **Gemini Antigravity** (native `AGENTS.md` support).
> Keep this file short. Detail lives in `docs/`.

## Product
**GlowCue** — *Know your skin. Choose with confidence.* A cosmetic skincare discovery and e-commerce assistant for the
[YouCam API Skin AI & eCommerce VTO Hackathon](https://youcam-api-skin-ai-ecommerce.devpost.com/). The flow is:
1. A selfie is analysed by **YouCam AI Skin Analysis v2.1 (SD, 10 concerns)**.
2. GlowCue explains the results and builds the **smallest, budget-fitting AM/PM routine** from a demo catalogue, skipping products the user already owns.
3. Every product comes with a receipt explaining why it was picked.
4. The whole routine goes into the cart with a transparent total.

Positioning is **Nigeria-first with NGN prices** (provisional default). Products are **fictional and labelled "GlowCue Demo"**.
**Deadline: Mon 2 Nov 2026, 17:45 WAT** (internal target 14:00 WAT).

## Non-negotiables
1. **Cosmetic, not medical.** Never diagnose, treat or cure. Use phrases like "helps the look of". Banned words are listed in `docs/RECOMMENDATION_ENGINE.md`.
2. **Secrets stay server-side.** The YouCam key exists only in `backend/.env` (owner-edited, gitignored) and Render env vars. Never read, print, log or commit it.
3. **Photos are personal data.** Process them in memory, strip EXIF, never write them to disk or logs, and never commit them without owner approval.
4. **No invented API behaviour.** Use only facts tagged [V] in `docs/YOUCAM_API.md`. In the scores, **higher means healthier**, and ranking uses `raw_score`.
5. **Units are scarce.** Default to mock mode. Live calls need the owner's explicit approval each time.
6. **Never claim something works without evidence.** Record real test output in `docs/PROJECT_STATUS.md`.

## Stack and layout
| Part | Tech | Path |
|---|---|---|
| Backend API | Python 3.14, FastAPI, Pydantic v2, httpx, Pillow, pytest, ruff | `backend/` |
| Frontend | React + TypeScript + Vite + Tailwind CSS v4, ESLint | `frontend/` |
| Repo tooling | secret scanner, project validator, guard tests | `scripts/` |
| Knowledge base | product, API, architecture, plans, prompts | `docs/` (index: `docs/README.md`) |

## Commands (run from the repo root)
```bash
backend/.venv/Scripts/python -m pytest backend/tests scripts/tests -q   # all Python tests
backend/.venv/Scripts/python -m ruff check backend scripts               # lint
cd backend && .venv/Scripts/python -m uvicorn app.main:app --reload     # API on :8000 (mock mode default)
cd frontend && npm run dev | npm run lint | npm run typecheck | npm run build
python scripts/validate_project.py                                      # config + docs integrity
python scripts/security/check_secrets.py --all                          # secret scan
```

## File ownership (prevents conflicting edits)
- **Claude Code** writes application code, tests, config and docs.
- **Antigravity** is a **reviewer**. It runs the app in a browser and writes findings **only** to `docs/qa/`. It edits source only on an `ag/*` branch the owner explicitly assigns, and only while Claude Code is idle.
- Only one writer works at a time. Hand over at a clean `git status` with a commit.

## Git
- `main` receives only reviewed PRs, merged by the owner. **GitHub branch protection is not yet enabled.** Configure it right after PR #1 merges (require a PR and the 3 CI checks, block force-push). Until then this rule is enforced by convention and the agent permission rules. Work happens on `chore/*`, `docs/*`, `feat/*`, `fix/*` and `test/*` branches.
- Use Conventional Commits (`feat: …`, `fix: …`).
- Never force-push, merge PRs, skip hooks or change repo settings. Those are the owner's actions.

## Definition of done
Acceptance criteria met, with tests added and green. Lint, typecheck and build pass. The secret scan is clean. The page works at 375 px and 1280 px when it's UI. Docs and `docs/PROJECT_STATUS.md` are updated. The change is committed on a feature branch.
