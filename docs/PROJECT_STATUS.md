# Project Status

> The live record of where GlowCue stands. Every Claude Code session starts here (via `/project-orchestrator`) and every task ends by updating it.
> **Rule:** only record results backed by command output. Planned is not the same as implemented.

**Last updated:** Sat 31 Oct 2026, 18:10 WAT (Claude Code)
**Deadline:** Mon 2 Nov 2026 17:45 WAT (11:45 EST) · **Internal target:** Mon 2 Nov 14:00 WAT · **Feature freeze:** Sun 1 Nov 21:00 WAT

## Current position
| | |
|---|---|
| Current phase | **Phase 0: Foundation** ([gate](implementation/PHASE_0_FOUNDATION.md)), complete locally, awaiting owner review |
| Current branch | `chore/project-foundation` |
| Next task | Phase 1: [02-backend-architecture](prompts/02-backend-architecture.md) on `feat/backend-api` |
| Product features implemented | **None yet.** Only `/api/health` and a placeholder page exist. |

## Phases
| Phase | Status | Evidence / PR |
|---|---|---|
| 0 Foundation | ✅ done locally (PR pending remote) | See "Latest test results" |
| 1 Backend core | ⏳ not started | — |
| 2 YouCam API + probe | ⏳ blocked on owner key rotation and approval | — |
| 3 Engine | ⏳ | — |
| 4 Frontend | ⏳ | — |
| 5 Integration & QA | ⏳ | — |
| 6 Release | ⏳ | — |
| 7 Submission | ⏳ | — |

## Latest test results (31 Oct 2026, 18:08 WAT)
| Check | Result |
|---|---|
| `pytest backend/tests scripts/tests -q` | **65 passed** (7 backend, 58 guard/scanner tests) |
| `ruff check` / `ruff format --check` (backend, scripts, hooks) | clean / 14 files formatted |
| `npm run lint` / `typecheck` / `build` | clean / clean / built in 228 ms (220 kB JS) |
| `npm audit --omit=dev` | 0 vulnerabilities (dev tooling: 11 moderate, not shipped, review later) |
| `python scripts/validate_project.py` | **267 checks passed, 0 failed** |
| `check_secrets.py --all` / pre-commit `--staged` | OK / OK |
| Live guard smoke tests in Claude Code | 4/4 blocked as designed (.env read, live-call keyword, secret write, Read deny) |
| Pre-commit photo guard | blocked a staged `.jpg` outside approved folders (exit 1) |
| Backend live health check | `GET /api/health` returns `{"status":"ok","mode":"mock"}` |

## Blockers and owner actions
| # | Action (owner) | Why | Blocks |
|---|---|---|---|
| O1 | **Rotate the YouCam API key**: console → API Keys → new key → delete old → paste the new one into `backend/.env` yourself | The first key was exposed in chat | Phase 2 live probe |
| O2 | **Install the GitHub CLI and log in:** `winget install --id GitHub.cli` → restart terminal → `gh auth login` | Lets Claude open PRs | Remote PRs |
| O3 | **Create an empty public GitHub repo `glowcue`** (no README or licence) and share the URL | Remote for PRs and CI | Remote PRs |
| O4 | **Fix the git author email:** the global `user.email` is a literal placeholder (`your-private-noreply@users.noreply.github.com`). Set your real GitHub no-reply address: `git config --global user.email "<id>+<username>@users.noreply.github.com"` | Commits should be attributed to you | Before first push |
| O5 | Restart Claude Code (or run `/hooks`) once, so all project skills, agents and hooks load fresh | Config created mid-session | — |
| O6 | Take 2–3 good selfies (front-facing, even light, face fills > 60% of width) | Live probe and demo | Phase 2 |

## Decisions
| Decision | Status |
|---|---|
| Positioning Nigeria-first, NGN ([ADR-003](decisions/ADR-003-product-catalogue.md)) | Provisional default (owner may revise before Phase 3) |
| Fictional "GlowCue Demo" catalogue (ADR-003) | Provisional default |
| Sample-mode photo: owner's selfie vs neutral silhouette | **Awaiting owner** (asked in prompt 04) |
| Special-award eligibility (Women in Tech / Rising Star), team composition | **Not asserted.** Awaiting owner confirmation before submission. |

## YouCam units ledger
| Date | Purpose | Δ units | Balance |
|---|---|---|---|
| 31 Oct 17:11 | Free balance check (no charge) | 0 | 1000 (expires 2027-01-29) |

## Pull requests
| PR | Branch | Status |
|---|---|---|
| #1 Foundation | `chore/project-foundation` | Prepared locally; needs O2 + O3 |

## Change log
| When (WAT) | Change |
|---|---|
| 31 Oct 18:10 | Phase 0 foundation built: engineering system, docs, skeletons, CI, guards |
| 31 Oct 18:05 | Fixed a false positive in `guard_bash.py` (prose in commit messages matched the .env and live-call rules); added regression tests |
