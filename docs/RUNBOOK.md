# Runbook

Practical "how do I…" for the owner. Commands run from the repo root in Git Bash unless noted.

## First-time local setup
```bash
git config core.hooksPath .githooks                 # enable the pre-commit secret scan (once per clone)
cd backend && python -m venv .venv && .venv/Scripts/python -m pip install -r requirements-dev.txt && cd ..
cd frontend && npm install && cd ..
cp frontend/.env.example frontend/.env.local        # VITE_API_BASE_URL=http://localhost:8000
```
**The YouCam key** is the owner's job. Open `backend/.env` in VS Code and set `YOUCAM_API_KEY=<fresh key>`. Agents never open this file. Mock mode works without a key.

## Run locally
| What | Command | URL |
|---|---|---|
| Backend (mock mode, default) | `cd backend && .venv/Scripts/python -m uvicorn app.main:app --reload --port 8000` | http://localhost:8000/api/health · Swagger: http://localhost:8000/docs |
| Frontend | `cd frontend && npm run dev` | http://localhost:5173 |
| Backend live mode (spends units; owner only) | add `YOUCAM_MODE=live` to `backend/.env`, then restart | — |

## Checks
```bash
python scripts/validate_project.py                    # config/docs integrity
python scripts/security/check_secrets.py --all        # secrets in tracked files
backend/.venv/Scripts/python -m pytest backend/tests scripts/tests -q
cd frontend && npm run lint && npm run typecheck && npm run build
```

## Everyday Claude Code usage
| You want to… | Type in Claude Code |
|---|---|
| Know where we are and what's next | `/project-orchestrator` |
| Run the next task | `/phase-execution docs/prompts/NN-name.md` |
| Check everything works | `/test-and-verify all` |
| Review UI quality | `/design-review` (then run the Antigravity prompt it gives you) |
| Security pass | `/security-review` |
| Open a PR for finished work | `/pr-workflow` |
| Deploy (manual) | `/deployment-release` |
| Prepare the submission (manual) | `/hackathon-submission check` |

## Checking YouCam units (free)
Ask Claude to "check the YouCam balance". It will ask you to approve, because even free calls go to the API host. Or check the console's usage page.

## Troubleshooting
| Symptom | Likely cause | Fix |
|---|---|---|
| `401 Invalid API key` | Old or rotated key, or a missing space after `Bearer` | Paste the fresh key into `backend/.env` (and Render) |
| `CreditInsufficiency` | Units exhausted | Kill switch to sample mode. Claim the social-sharing bonus. |
| `error_src_face_too_small` | Face < 60% of image width | Crop closer, portrait orientation |
| `error_lighting_dark` | Dim photo | Face a window, even light |
| Frontend "Network error" in prod | CORS origin mismatch, or Render asleep | Set `FRONTEND_ORIGIN` to the exact Vercel URL. Wait ~50 s for the cold start. |
| Commit blocked by pre-commit | Secret or forbidden file staged | Unstage it (`git restore --staged <file>`), fix, recommit. **Never** use `--no-verify`. |
| Claude says "BLOCKED by GlowCue guard" | A guard rule matched | Read the reason. If the action is truly needed, you run it yourself or approve it explicitly. |

## Releases
| Date (WAT) | Commit | Backend URL | Frontend URL | Verification |
|---|---|---|---|---|
| — | — | — | — | not yet deployed |
