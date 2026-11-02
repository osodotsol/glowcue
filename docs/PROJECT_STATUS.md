# Project Status

> The live record of where GlowCue stands. Every Claude Code session starts here (via `/project-orchestrator`) and every task ends by updating it.
> **Rule:** only record results backed by command output. Planned is not the same as implemented.

**Last updated:** Mon 2 Nov 2026 (Claude Code): the full product (engine, sample and live analysis, consultation, report, ritual, shop, camera capture) is implemented and verified locally but **uncommitted**; it is planned as PR #2 once PR #1 is merged. See the dated sections below.
**Deadline:** Mon 2 Nov 2026 17:45 WAT (11:45 EST) · **Internal target:** Mon 2 Nov 14:00 WAT · **Feature freeze:** Sun 1 Nov 21:00 WAT

## Current position
| | |
|---|---|
| Repository | https://github.com/osodotsol/glowcue (public) |
| Current phase | **Phase 0: Foundation** ([gate](implementation/PHASE_0_FOUNDATION.md)) is in review as **PR #1** (pushed, CI green on `9ce7e63`, awaiting the owner's merge). The product work is local and uncommitted, waiting for PR #1 to merge. |
| Current branch | `chore/project-foundation` |
| Next task | After the owner merges PR #1 and authorises it: commit the product work as PR #2 (six commits), then deploy, record the demo video and submit |
| Product features implemented | **Built and tested locally, not yet committed:** sample-profile analysis; live YouCam analysis (one real analysis verified, off by default); the 4-step consultation; the skin report; the budget-optimised AM/PM ritual with receipts and swaps; the shop, bag and checkout preview; in-app camera capture. **Not built:** heatmaps and masks, and a Playwright smoke test. |
| Schedule | Submission day. Deadline Mon 2 Nov 17:45 WAT; internal target 14:00 WAT. Remaining: the owner's merge of PR #1, the PR #2 commits, deployment, the demo video and the Devpost entry. |

## Phases
| Phase | Status | Evidence / PR |
|---|---|---|
| 0 Foundation | 🔍 in review: PR #1 open and pushed (`9ce7e63`), all three CI checks green; awaiting the owner's merge | [PR #1](https://github.com/osodotsol/glowcue/pull/1) |
| 1 Backend core | ✅ built and tested locally (engine, catalogue, sample analysis, shop routes); **uncommitted**, planned for PR #2 | see "Edition 2 implementation" below |
| 2 YouCam API + probe | ✅ built and verified locally, including one owner-approved live analysis (1 Nov); live mode is off by default; **uncommitted** | see "Live YouCam integration" below |
| 3 Engine | ✅ built and tested locally; **uncommitted** | see "Edition 2 implementation" below |
| 4 Frontend | ✅ built and browser-tested locally, including camera capture and the professional footer; **uncommitted** | see "Camera capture and footer refinement" below |
| 5 Integration & QA | 🔄 local checks green (see the dated sections); the only known failure is a dev-server-only hero-video console message; Playwright smoke test not built | — |
| 6 Release | ⏳ not started: needs PR #1 merged, the PR #2 commits and deployment | — |
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

## Edition 2 implementation (1 Nov 2026, local, uncommitted)
Approved design: the private design canvas (Edition 2). Decisions: [ADR-005](decisions/ADR-005-demo-provider-and-redesign.md). Images: [ASSETS.md](ASSETS.md).

| Stage | Done | Browser QA (headless Chrome, 1280 and 390 px) |
|---|---|---|
| 1 Foundation | Immutable cart updates; reset leaves storage empty; hash navigation (Back, Forward, reload); self-hosted Fraunces and Inter; `Card padded={false}`; Edition 2 tokens and shared components | 13/13 |
| 2 Brand and onboarding | Portrait-led landing, header and footer, four-stage consultation (`#/about/1–4`), selfie with local preview and demo "skin stories" | 65/65 |
| 3 Skin report | Band-count overview (no averaged score), priorities, attribute explorer with 60/75 scale, nine glow arcs, "skin map: live analysis only"; mobile tab bar after the report | 29/29 (arcs checked against the API) |
| 4 Routine and commerce | AM (sky) / PM (cocoa) rituals with photo steps, receipts and in-place swaps; collapsible mobile preferences; shop filters and quick-add; bag drawer (desktop) and sheet (mobile), modal with focus trap; full bag page; checkout preview with ritual card | 45/45 (totals checked against server quotes) |
| 5 Motion | Hero arch reveal, headline rise, page and AM/PM View Transitions, arc fill and band-bar grow, add-to-bag flight and counter bump, drawer slide; all off under reduced motion | 15/15 |
| Hero film | Owner's AI-generated clip replaces the static P1 hero (desktop arch and mobile opening): muted, looping and inline, with a poster still; a still image under reduced motion; a placeholder if the file is missing. Its baked-in white side bars are cropped out | 25/25 (bars hidden, video playing, reduced-motion still, no overflow, headline and CTA present; missing-file placeholder checked in a separate run) |
| Navigation | Slim sticky desktop bar (Discover · How it works · Shop · My Routine once a report exists · bag icon); mobile logo, bag and menu panel (focus trap, Esc, tap outside, closes on navigation and on Back); `#/how` route scrolls to the How-it-works section; post-report tab bar unchanged; guest-first, no accounts | 89/89 at 1280, 390 and 360 px; stage 1–5 suites re-run: 13 + 65 + 29 + 45 + 15 all pass after updating three assertions to the approved video hero and icon bag |

Other checks: backend 123 passed · guard tests 367 passed, 3 xfailed · ruff clean · validator 307/307 · secret scan OK · frontend lint, typecheck and build clean (JS 92 KB gzipped) · production dependencies: 0 vulnerabilities.

Limitations: the portraits and hero film have an unverified licence (O9); they are published from `frontend/public/brand/` by the owner's decision of 2 Nov 2026. The renders read as clean 3D, not lens photography. View Transitions need a supporting browser (others switch instantly).

## Live YouCam integration, Phase A (1 Nov 2026, offline build, uncommitted)
Design: [ADR-006](decisions/ADR-006-live-youcam-analysis.md). Facts and open questions: [YOUCAM_API](YOUCAM_API.md) §6.9. Safeguards B1–B6: [SECURITY_PRIVACY](SECURITY_PRIVACY.md) §4.4.

**Built:**
- the YouCam client: upload registration, presigned PUT, v2.1 task with `format:"json"`, 10 s polling, task delete;
- the credit-floor check, in-memory image validation and EXIF removal, the normaliser for 9 SD actions, the error table, daily caps;
- `POST /api/analyses` and `GET /api/analyses/{id}`;
- the consent and progress UI with retake guidance and the demo alternative, plus honest live labels on the report;
- the probe script, written but **not run**.

**No live request has been made and no units used.** Live analysis is off by default.

**Tests:**

| Check | Result |
|---|---|
| Backend pytest | 189 passed (66 new) |
| Ruff | Clean |
| Browser suite, live UI (intercepted API, backend in mock mode) | 45/45 at 1280 and 390 px |
| Edition 2 suites | Stage 3 29/29, stage 4 45/45, navigation 91/91. Stages 1, 2 and 5: all functional checks pass. The only failure is a headless-Chrome cache message for the hero video (`ERR_CACHE_OPERATION_NOT_SUPPORTED` on `glowcue-hero.mp4`), unrelated to this work. |
| Frontend lint, typecheck, build | Clean |

### Balance check and parser fix (1 Nov 2026)
**First live balance-only check:**
- HTTP 200, so the key was accepted.
- GlowCue's client returned `bad_response`: it expected a `data` wrapper that this endpoint doesn't use.
- 0 units used. Safe mode restored and verified (`YOUCAM_MODE=mock`, live off, key present).

**Offline fix:**
- `parse_balance()` reads the verified `results[]` format, preferring `amount_dec` and falling back to `amount`.
- Everything else fails closed as `credit_unknown`, with a structure-only diagnostic (no values).
- Details in [YOUCAM_API](YOUCAM_API.md) §6.10.

**Tests:** backend **210 passed**, `test_youcam_client.py` **43 passed**, Ruff clean.

**Second live balance-only check (owner-approved):** HTTP 200; the corrected parser read the response. Balance **1040.00 units**. 0 units used. Safe mode restored and verified.

**No-face task (owner-approved, one task):**
- The v2.0 upload, then v2.1 task flow, works.
- The task returned `error_no_face`, and the delete was accepted.
- 14.2 s end to end; **0 units** (balance still 1040.00).
- Safe mode restored and verified.
- Details in [YOUCAM_API](YOUCAM_API.md) §6.8.

### First successful live analysis (1 Nov 2026)
- Three owner-approved selfie attempts. The first two were rejected for framing (`error_src_face_too_small`, then `error_src_face_out_of_bound`) at 0 units.
- The third **succeeded**:
  - all 9 SD concerns returned inline as JSON, with no regions;
  - 14 units (balance now 1026.00);
  - 17.3 s;
  - delete accepted.
- Safe mode was restored after each run and verified with the settings-only check.
- Facts and response structure: [YOUCAM_API](YOUCAM_API.md) §6.11. No scores or photo details are kept in docs.

### Phase D1: release fixes and product refinement (1 Nov 2026, uncommitted)
- **Private assets:**
  - production builds no longer contain or reference `public/private/` (Vite plugin plus code gating);
  - production uses cleared renders;
  - a build-time leak check is added;
  - verified on a fresh build and in the production build in a browser.
- **Report headline:** derived from band counts (`frontend/src/lib/reportHeadline.ts`, 12 Node tests). "Mostly comfortable" is gone. The dark-spots description and noun are corrected.
- **Budget decision:** a one-sentence summary from the server's numbers (budget, cost, money left, coverage); "not covered at this budget" sits in the same card; coverage is labelled "of flagged concerns".
- **Shelf:** owned cleanser, moisturiser and sunscreen appear as unverified "From your shelf" steps (never in the bag). An owned serum gets a note.
- **README:** rewritten for the positioning.

### Final critical fixes (2 Nov 2026, uncommitted)
- **Upload endpoint:**
  - cheap checks (consent, type, size, signature) come first;
  - daily capacity is reserved **before** decoding;
  - Pillow runs in a worker thread, at most 2 at once (`503 busy` otherwise);
  - any failure after the reservation releases it.
  - Tests: 7 new, including a concurrency test and an event-loop test shown to fail if decoding returns to the loop.
- **CORS:** `APP_ENV=production` allows only `FRONTEND_ORIGIN` and refuses a localhost value; development keeps the local origins. Tests: 7 new.
- **Copy:**
  - "Not sure yet" replaces "Not sure: let the analysis decide" (live analysis doesn't measure skin type);
  - the skin-map card now says the report gives scores, not a face map.
- **Docs:** PRD, ARCHITECTURE and DESIGN_SYSTEM now mark the heatmap, masks, sample mode and Playwright smoke test as not implemented.

### Camera capture and footer refinement (2 Nov 2026, uncommitted)
- **In-app selfie camera** (`frontend/src/components/CameraCapture.tsx`, helpers in `frontend/src/lib/camera.ts`):
  - opens only when "Take a selfie" is tapped (front camera, no audio), with a live preview, oval guide, tips, capture, retake and accept;
  - every camera track stops on capture, close, Esc, unmount and page hide; nothing is recorded, and the frame stays a local blob;
  - the captured photo passes the same type and 10 MB checks as a chosen file, then the unchanged `prepareSelfie` and server checks; upload still needs consent;
  - "Choose an existing photo" keeps the file picker; browsers without a camera API fall back to the system camera input;
  - declined permission, no camera and a busy camera each show a message with "Choose a photo instead".
- **Disclosures:** the "Demo build" footer paragraph is gone (the footer was later redesigned, see the wording pass below). Sample profiles are introduced on the selfie page, the shop has one catalogue note, and the bag, cart and checkout say "no payment is processed" next to the checkout action.
- **Results (local):** frontend lint and typecheck clean; `npm test` 18 passed (6 new camera tests); build plus asset-leak check OK; camera browser suite 50/50 with Chrome's fake camera (no `/api/analyses` request and no off-machine request); live-ui 45/45, d1 58/58, stage4 45/45, nav 90/91 (the known dev-server hero-video cache message); pytest 599 passed, 3 xfailed; secret scan OK; validator 324/324.

### Professional wording pass (2 Nov 2026, uncommitted)
- "Demo" no longer appears anywhere a customer can see it. Sample reports say *Sample report · <profile>* plus one quiet note that the scores are not an analysis of the photo. Live reports say *Your skin report*.
- Packshot labels now show a volume instead of "DEMO". The 20 images were re-rendered with `scripts/assets/render_products.py`; the originals are backed up outside the repo.
- The footer was redesigned: brand, Explore links, privacy points, © line and the cosmetic disclaimer. Technical copy ("checked on our server") was rewritten for shoppers.
- Backend customer messages now offer "a sample profile". The API field names (`is_demo`, `/demo-profiles`, brand `GlowCue Demo`) are unchanged.
- Results: npm test 18 passed; pytest 599 passed, 3 xfailed; ruff clean; secret scan OK; validator 324/324. Browser suites: camera 50/50, live-ui 45/45, d1 58/58, nav 91/91, stage4 44/45 (the known hero-video message).

### Privacy wording corrections (2 Nov 2026, uncommitted)
- Answers: now described as used to build recommendations, kept in this browser session and not saved to an account (footer, menu, consultation page, README).
- Photo deletion: GlowCue *requests* deletion from YouCam after processing. The request is accepted, but deletion cannot be independently verified, so no document or screen promises it. See [YOUCAM_API.md](YOUCAM_API.md).
- README report labels now match the interface ("Sample report" / "Your skin report"); the header and phases table above were brought up to date.

### Brand visuals restored to production (2 Nov 2026, uncommitted)
- **Why:** the production build showed studio renders where the local app shows the two portraits and the hero film. The owner asked for the original visuals to be public.
- **What:** `p2-consultation.webp`, `p3-storytelling.webp`, `glowcue-hero.mp4` and `glowcue-hero-poster.webp` were copied unchanged from `frontend/public/private/` to `frontend/public/brand/` and are read from `/brand/...`. Placement, crops, the hero frame box and the reduced-motion poster are unchanged. The three unused private files stay local. The 20 approved product and scene images are untouched.
- **Guard:** `check-build-assets.mjs` still blocks `private/` and any `/private/` reference, and now also requires `dist/brand/` to hold exactly the four approved files (checked against five deliberately broken builds).
- **Rights:** the licence of these files is **not verified** (O9). This is an owner-approved exception, recorded in [ASSETS.md](ASSETS.md).
- **Photo guard:** on the owner's instruction, `scripts/security/secret_patterns.py` now allows exactly these brand files (`PHOTO_ALLOWED_FILES`); every other photograph outside the approved folders, including anything else in `frontend/public/brand/`, is still refused. Ten new guard tests cover the allowed and still-blocked paths.

### Friendlier connection errors and photo-consent wording (2 Nov 2026)
- **Errors:** a failed request now shows "We're having trouble connecting." with "Check your internet connection or move somewhere with a stronger network, then try again." Gateway failures (502/503/504) say "GlowCue is temporarily unavailable." instead, and other failures without a message say "Something went wrong." Messages written by the API are kept as they are. Customers no longer see words like backend, server, API or localhost; status codes and the underlying error go to the browser console only (`frontend/src/lib/errors.ts`, `lib/api.ts`). The landing page, shop, routine, cart, selfie page and live-analysis error box share this wording.
- **Consent:** the checkbox now reads "I agree to send this photo to Perfect Corp (YouCam) for automated skin analysis." and the explanation sits directly under it: processed temporarily, not stored by GlowCue, GlowCue requests deletion from YouCam, and GlowCue cannot independently verify that deletion. Consent is still required before upload and the Analyse button stays disabled until it is given.
- **Known behaviour, unchanged:** if the connection drops while a live analysis is already running, "Try again" starts a new upload, which could be a second analysis.

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
| O9 | Confirm the licence of the published portraits and hero film (or replace them with cleared photographs) and fill the table in [ASSETS.md](ASSETS.md) | Owner | Public release: the files are already published by owner decision (2 Nov), licence unverified |
| O10 | Approve how to commit the current work (security stage and product slice plus Edition 2) | Owner | PR |
| O11 | Review Phase A, then authorise the first controlled live test (probe steps in the Phase A report). Live mode is switched on only by you, in `backend/.env` | Owner | Phase B |

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
| 2 Nov | Final fixes: upload capacity reserved before decoding (worker-thread decode), production CORS, honest skin-type and skin-map copy, planning-doc corrections |
| 1 Nov | Phase D1: private assets kept out of production builds (plus a leak check), band-based headline, budget decision summary, shelf steps, README rewrite |
| 1 Nov | First successful live SD analysis: 9 concerns inline, 14 units, 17.3 s, delete accepted; safe mode verified |
| 1 Nov | Two selfie attempts: `error_src_face_too_small`, then `error_src_face_out_of_bound` (framing); 0 units; safe mode verified. A successful analysis is still unverified |
| 1 Nov | No-face task: v2.0 upload, then v2.1 task works; `error_no_face`; delete accepted; 0 units (balance 1040.00) |
| 1 Nov | First live balance check (200, key accepted, `bad_response`, 0 units); balance parser fixed offline (210 tests pass); second check read the balance (1040.00), 0 units |
| 1 Nov | Phase A: offline live-analysis integration (client, safeguards B1–B6, routes, consent UI, tests); consultation labels corrected; no live calls |
| 1 Nov | Responsive navigation (desktop bar, mobile menu, `#/how` section route); P2 consultation portrait replaced (local, uncommitted) |
| 1 Nov | Hero film integrated on the landing page (local, git-ignored asset, uncommitted) |
| 31 Oct 22:00 | Round-2 security hardening: default-ask live-call gate, protected-file coverage including interpreter and patch routes, fail-closed hooks (`onFailure: block`), network and credential isolation for backend tests, honest docs with backend requirements B1-B6 |
| 31 Oct 21:25 | PR #1 review corrections: real permission prompt for live calls and guardrail edits; doc consistency fixes (`b5a4362`) |
| 31 Oct ~20:30 | Commits re-attributed (trees verified identical); repo created; branches pushed; PR #1 opened; CI green |
| 31 Oct 18:10 | Phase 0 foundation built: engineering system, docs, skeletons, CI, guards |
| 31 Oct 18:05 | Fixed a false positive in `guard_bash.py` (prose in commit messages); added regression tests |
