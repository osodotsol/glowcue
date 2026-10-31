## Purpose
<!-- Why this change exists. One or two sentences. -->

## Summary of changes
<!-- Bullet list of what changed. -->

## Related phase / prompt / issue
<!-- e.g. Phase 3 · docs/prompts/06-recommendation-engine.md · Closes #n -->

## Implementation notes
<!-- Non-obvious decisions, trade-offs, ADR links. -->

## Acceptance criteria
<!-- Copy from the prompt's gate. Mark each with evidence. -->
- [ ] … — evidence:

## Tests
<!-- Paste REAL summary lines from this branch. -->
| Check | Command | Result |
|---|---|---|
| Backend tests | `cd backend && .venv/Scripts/python -m pytest -q` | |
| Guard tests | `backend/.venv/Scripts/python -m pytest scripts/tests -q` | |
| Lint / format | `ruff check` · `ruff format --check` · `npm run lint` | |
| Typecheck / build | `npm run typecheck` · `npm run build` | |
| E2E (when present) | `npx playwright test` | |

## Screenshots (UI changes)
<!-- 375 px and 1280 px. No faces without consent, no keys. -->

## Security checklist
- [ ] No secrets, `.env` files or keys in the diff (`python scripts/security/check_secrets.py --all` is clean)
- [ ] No personal photos committed (or owner-approved sample only)
- [ ] Uploads stay in memory; no image data in logs
- [ ] No live YouCam calls in tests; any live usage was owner-approved and recorded
- [ ] `security-reviewer` run if uploads, config, CI or secrets changed

## Documentation checklist
- [ ] `docs/PROJECT_STATUS.md` updated with real results
- [ ] Contracts in sync (`docs/API_CONTRACTS.md`, `app/models.py`, `frontend/src/lib/types.ts`)
- [ ] ADR added for any decision change
- [ ] Nothing planned is described as implemented

## Outstanding issues
<!-- Known gaps, follow-ups, deferred findings. -->

## Reviewer checklist
- [ ] Scope matches the task; no unrelated refactors
- [ ] New behaviour has tests that would fail without it
- [ ] Copy is cosmetic (no medical claims); demo/sample labels present
- [ ] CI green
