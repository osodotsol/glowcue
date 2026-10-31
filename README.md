# GlowCue

**Know your skin. Choose with confidence.**

GlowCue turns a selfie analysed by **Perfect Corp's YouCam AI Skin Analysis API** into the *smallest, budget-fitting* morning and evening skincare routine, skips products you already own, and explains why each product was picked. Then it adds the whole routine to your cart with a transparent total.

> **Project status: engineering foundation in place; product features are under construction.**
> See [docs/PROJECT_STATUS.md](docs/PROJECT_STATUS.md) for what is actually implemented. Built for the
> [YouCam API Skin AI & eCommerce VTO Hackathon](https://youcam-api-skin-ai-ecommerce.devpost.com/).

> **Cosmetic guidance only — not medical advice.** Products shown are fictional **"GlowCue Demo"** items with illustrative prices.

## What it will do
1. **Analyse:** upload a selfie with consent. YouCam AI Skin Analysis v2.1 measures 10 cosmetic attributes.
2. **Understand:** see your top priorities, ranked on YouCam's raw model score (the honest one), with YouCam's own detection heatmaps.
3. **Optimise:** set a budget and tick what you already own. GlowCue tests every valid product combination and picks the smallest routine with the highest coverage.
4. **Shop:** follow the AM/PM routine with a receipt for each product, then add it all to the cart.

## Repository layout
| Path | What |
|---|---|
| `backend/` | FastAPI API (Python). Holds the YouCam key server-side. |
| `frontend/` | React + TypeScript + Vite + Tailwind CSS v4 single-page app |
| `docs/` | Knowledge base: product, architecture, API notes, plans, prompts ([index](docs/README.md)) |
| `scripts/` | Project validator, secret scanner, guard tests |
| `.claude/`, `AGENTS.md`, `CLAUDE.md`, `.agents/` | AI-assisted engineering system: rules, skills, review agents, safety hooks |

## Quick start (mock mode, no API key needed)
```bash
git config core.hooksPath .githooks
cd backend && python -m venv .venv && .venv/Scripts/python -m pip install -r requirements-dev.txt
.venv/Scripts/python -m uvicorn app.main:app --reload        # http://localhost:8000/api/health
cd ../frontend && npm install && npm run dev                 # http://localhost:5173
```
On macOS or Linux, use `.venv/bin/python`. Live analysis needs a YouCam API key in `backend/.env` (see [backend/.env.example](backend/.env.example)) and is off by default.

## Quality checks
```bash
python scripts/validate_project.py
python scripts/security/check_secrets.py --all
backend/.venv/Scripts/python -m pytest backend/tests scripts/tests -q
cd frontend && npm run lint && npm run typecheck && npm run build
```

## Privacy
Photos are processed in memory, stripped of metadata, never stored by GlowCue, and processed only with explicit consent. See [docs/SECURITY_PRIVACY.md](docs/SECURITY_PRIVACY.md).

## License
[MIT](LICENSE)
