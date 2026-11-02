# Project Status

> The live record of where GlowCue stands. Every Claude Code session starts here (via `/project-orchestrator`) and every task ends by updating it.
> **Rule:** only record results backed by command output. Planned is not the same as implemented.

**Last updated:** Sat 31 Oct 2026, 22:00 WAT (Claude Code)
**Deadline:** Mon 2 Nov 2026 17:45 WAT (11:45 EST) · **Internal target:** Mon 2 Nov 14:00 WAT · **Feature freeze:** Sun 1 Nov 21:00 WAT

## Current position
| | |
|---|---|
| Repository | https://github.com/osodotsol/glowcue (public) |
| Current phase | **Phase 0: Foundation** ([gate](implementation/PHASE_0_FOUNDATION.md)), in review as **PR #1**. Two local follow-up commits are awaiting the owner's push approval. |
| Current branch | `chore/project-foundation` |
| Next task | After PR #1 merges: Phase 1, [02-backend-architecture](prompts/02-backend-architecture.md), on `feat/backend-api` (mock mode, no API calls) |
| Product features implemented | **None yet.** Only `/api/health` and a placeholder page exist. |
| Schedule | **Behind plan by about 2.5 h.** The roadmap §18 expected the engine work to be under way by Sat 21:00. Recovery: start Phase 1 immediately after the merge, and apply the cut list in [roadmap §18](IMPLEMENTATION_ROADMAP.md) if still behind on Sunday morning. |

## Phases
| Phase | Status | Evidence / PR |
|---|---|---|
| 0 Foundation | 🔍 in review: PR #1 open, CI green on `c1b1704`. Local only (not pushed): `b5a4362` (first review corrections) and the second security-hardening commit | [PR #1](https://github.com/osodotsol/glowcue/pull/1) |
| 1 Backend core | ⏳ not started | — |
| 2 YouCam API + probe | ⏳ not started; needs the owner's per-call approval prompt for the live probe | — |
| 3 Engine | ⏳ | — |
| 4 Frontend | ⏳ | — |
| 5 Integration & QA | ⏳ | — |
| 6 Release | ⏳ | — |
| 7 Submission | ⏳ | — |

## Completed setup (owner and agent)
| Item | Status | Evidence |
|---|---|---|
| Replacement YouCam key in `backend/.env` | ✅ done by owner | Checked through `Settings` without revealing the value: present, `sk-` form, no whitespace. File untracked and ignored. |
| GitHub CLI installed and authenticated | ✅ | `gh` 2.103.3, logged in as `osodotsol` (scopes: repo, read:org, gist) |
| Git identity | ✅ | Global `user.email` = `283860466+osodotsol@users.noreply.github.com`, name `Oti Samuel Osondu` |
| Commits re-attributed | ✅ | Trees identical to the originals (`522deed…`, `261b459…`). Local backups `backup/main-pre-rewrite` and `backup/foundation-pre-rewrite` (not pushed). |
| Public repo created, `main` and branch pushed, PR #1 opened | ✅ | CI first run: repo checks ✅ · backend ✅ · frontend ✅ |
| PR #1 review corrections (round 1: `b5a4362`, round 2: security hardening) | ✅ done locally, awaiting an independent Opus security review and the owner's approval to push | see "Latest test results" |

## Latest test results (31 Oct 2026, ~21:55 WAT, round-2 hardening commit, run locally)
| CI-equivalent job | Command(s) | Result |
|---|---|---|
| Repo checks | `validate_project.py` · `check_secrets.py --all` / `--history` · `pytest scripts/tests` | **306 checks passed, 0 failed** · OK / OK · **239 passed, 3 xfailed** (the 3 are documented known limitations, strict) |
| Backend | `ruff check .` · `ruff format --check .` · `pytest` (in `backend/`) | clean · clean · **19 passed** (7 original + 12 network/credential-isolation tests) |
| Frontend | `npm ci` · `lint` · `typecheck` · `build` | clean · clean · built in 216 ms |
| Extra (not yet in CI) | `ruff check` + `format --check` on `backend/`, `scripts/`, `.claude/hooks/` | clean |
| Combined Python run | `pytest scripts/tests backend/tests` | **258 passed, 3 xfailed** |

What the guard tests now prove (all assert the exact decision, in-process and through the real hook protocol):
- every one of the 32 bypass attempts from the review of `b5a4362` has a regression test (marked `REVIEW`), covering wrappers (`bash -c`, `sh -c`, `powershell -Command`, `cmd /c`, `timeout`, `nice`, `command`, `env`, `xargs`, `uv run`, subshells, pipes), runtime-built hosts, settings-driven calls, `python -m` modules, Node scripts, curl config files, helper imports, mode-switch routes, and interpreter and patch-file writes to guardrails;
- the old approval token and any other variable cannot bypass the prompt, and the token no longer exists in the guards;
- hard denies win over asks;
- fail-closed behaviour: malformed input, wrong shapes, wrong types, internal exceptions, a missing pattern module, a crashing hook script and a missing interpreter (the exact `settings.json` command is executed) all end in a prompt or a block;
- `settings.json` wiring: `onFailure: block`, `|| exit 2`, matchers, native ask and deny rules, no bypass mode;
- known limitations are strict expected-failures, so any change in behaviour is noticed.

Backend tests cannot read `backend/.env` or reach the network: attempts through sync and async httpx, raw sockets, DNS and urllib are all blocked, while `MockTransport` and `TestClient` still work.

## Outstanding tasks and owner actions
| # | Action | Owner | Blocks |
|---|---|---|---|
| O1 | **Confirm in the YouCam console that the first (exposed) key is deleted** and only the new key remains | Owner | Peace of mind; can't be verified by the agent |
| O2 | Review PR #1 (including the correction commit), then merge it yourself | Owner | Phase 1 |
| O3 | **Enable branch protection on `main` right after merging:** Settings → Branches (or Rules) → require a pull request, require status checks (repo checks, backend, frontend), block force-push | Owner | Safety for every later PR |
| O4 | Take 2–3 good selfies (front-facing, even light, face fills > 60% of width) | Owner | Phase 2 probe |
| O5 | Later: delete the local backup branches and `refs/original` once you're happy with the rewritten history | Owner approval | — |
| O6 | Decide whether the sample photo is your selfie or a neutral silhouette (asked in prompt 04) | Owner | Phase 2 |
| O7 | **Tell me whether you saw a permission prompt** for the harmless check command containing the word `yce-api` (it printed text only and made no network call), and for my edits to hook, settings and test files. If you saw none, the gate does not reach you in your current mode and must be revisited before Phase 2. | Owner | Trusting the live-call gate |
| O8 | On prompts about YouCam or guardrails, choose the one-time **Yes**, never "don't ask again" | Owner | L1 |

## Decisions
| Decision | Status |
|---|---|
| Positioning Nigeria-first, NGN ([ADR-003](decisions/ADR-003-product-catalogue.md)) | Provisional default (owner may revise before Phase 3) |
| Fictional "GlowCue Demo" catalogue (ADR-003) | Provisional default |
| Live-call approval = owner permission prompt (hook `"ask"`), no tokens ([ADR-002](decisions/ADR-002-api-integration.md)) | ✅ Adopted after the PR #1 review |
| Sample-mode photo: owner's selfie vs neutral silhouette | **Awaiting owner** (O6) |
| Special-award eligibility (Women in Tech / Rising Star), team composition | **Not asserted.** Awaiting owner confirmation before submission. |

## Review findings status
**Round 1** (review of the foundation, PR #1)
| # | Severity | Finding | Status |
|---|---|---|---|
| 1 | High | Live-call approval token could be self-applied | ✅ Fixed in `b5a4362`; hardened further in round 2 |
| 2 | Medium | `main` described as protected, but it isn't | ✅ Docs corrected; enabling protection is owner action O3 |
| 3 | Medium | PROJECT_STATUS stale | ✅ Rewritten, updated again here |
| 4 | Medium | Outdated blueprint prompt IDs | ✅ Replaced with links |
| 5 | Medium | Roadmap duplicated by gates and prompts | ✅ Authority note added |
| 6 | Medium | Reviewer agents have Bash, so "never edit" isn't technically enforced | ⏳ Open |
| 7 | Low | CI doesn't lint `scripts/` and `.claude/hooks/` | ⏳ Open |
| 8 | Low | Hooks fail open | ✅ Fixed in round 2 (see M3) |
| 9, 10 | Low | React version, F1/F2, push-protection claim | ✅ Fixed |
| 11 | Low | `.env.*` deny list narrower than the guard | ✅ Fixed in round 2: explicit variants plus `*.env`; example files stay readable |
| 12-14 | Low | Windows-only `.vscode` path; Actions pinned to tags; health endpoint shows mode | ⏳ Open (accepted for now) |

**Round 2** (adversarial security review of `b5a4362`)
| # | Severity | Finding | Status |
|---|---|---|---|
| H1 | High | Shell and process wrappers bypassed the live gate | ✅ Fixed: default-ask when a YouCam marker appears in any executing command; 24 wrapper forms plus runners tested |
| H2 | High | Backend tests could read the real key and the network | ✅ Fixed: `conftest.py` isolates settings from `backend/.env` and blocks outbound network; 12 proof tests |
| H3 | High | Guardrail files could be changed via interpreters, `git apply`, patch | ✅ Fixed: any non-read-only command naming a guardrail path asks; patch and script contents are read; `.gitignore`, CI workflows, guard tests, validator and `core.hooksPath` added to the protected list |
| M1 | Medium | Config-driven calls are invisible to command inspection | 📌 **Backend requirements B1-B6 recorded** ([SECURITY_PRIVACY §4.4](SECURITY_PRIVACY.md), prompts 02 and 03, phase gates 1 and 2). Not implemented yet, by design. |
| M2 | Medium | Mode switching without `YOUCAM_MODE=live`; non-`.env` env files writable | ✅ Hook asks for mode-switch routes; every env-style file is denied for edits. App-level part is B1. |
| M3 | Medium | Hooks fail open | ✅ Fixed: `onFailure: block`, `\|\| exit 2`, fail-closed code paths; each scenario tested |
| M4 | Medium | Docs overclaimed coverage | ✅ Rewritten with the protected list, known limits, backend safeguards, and why mock is the default |
| L1 | Low | "Don't ask again" may save an allow rule | 🔎 Investigated: per the docs, Bash approvals can be saved to `.claude/settings.local.json`; agent edits to that file are now denied; whether a saved rule silences a *hook* ask is undocumented. **Owner: choose the one-time "Yes" (O8).** |
| L2 | Low | Matcher covers only Bash and PowerShell | ✅ `Monitor` added. No other command-running tools are configured; extend the matcher if one is added. |
| L3 | Low | Tests didn't cover wrappers or fail-safe, and no real-prompt check | ✅ Tests added. 🔎 **Real-prompt check: see O7.** |

## YouCam units ledger
| Date | Purpose | Δ units | Balance |
|---|---|---|---|
| 31 Oct 17:11 | Free balance check, first key (no charge) | 0 | 1000 (expires 2027-01-29) |

No live calls have been made with the replacement key.

## Pull requests
| PR | Branch | Status |
|---|---|---|
| [#1](https://github.com/osodotsol/glowcue/pull/1) Foundation | `chore/project-foundation` | Open. CI green on `c1b1704`. **Two local commits ahead, not pushed:** `b5a4362` and the round-2 hardening commit. Awaiting an independent Opus security review and the owner's push approval. **Do not merge until reviewed by the owner.** |

## Change log
| When (WAT) | Change |
|---|---|
| 31 Oct 22:00 | Round-2 security hardening: default-ask live-call gate, protected-file coverage including interpreter and patch routes, fail-closed hooks (`onFailure: block`), network and credential isolation for backend tests, honest docs with backend requirements B1-B6 |
| 31 Oct 21:25 | PR #1 review corrections: real permission prompt for live calls and guardrail edits; doc consistency fixes (`b5a4362`) |
| 31 Oct ~20:30 | Commits re-attributed (trees verified identical); repo created; branches pushed; PR #1 opened; CI green |
| 31 Oct 18:10 | Phase 0 foundation built: engineering system, docs, skeletons, CI, guards |
| 31 Oct 18:05 | Fixed a false positive in `guard_bash.py` (prose in commit messages); added regression tests |
