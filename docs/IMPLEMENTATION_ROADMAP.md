# Implementation Roadmap, Timeline & Risk Register

> **Status:** planned design from the GlowCue blueprint (research snapshot 31 Oct 2026). Nothing here is implemented unless [PROJECT_STATUS](PROJECT_STATUS.md) says so. Tags: **[V]** verified, **[A]** assumption, **[R]** recommendation, **[U]** unresolved.

## 10. Chronological development roadmap

Times are WAT. Hours are focused working time.

### PHASE 0: Preparation & environment readiness (Sat 16:30–18:00, 1.5 h)
1. **Objective:** every account, key and tool is ready, so no blocking later.
2. **Importance:** the redeem code and key are the critical path. Forum history shows code issues.
3. **Actions (you):**
   1. Join the hackathon on Devpost.
   2. Redeem the code and create an API key; store it in a password manager.
   3. Check the balance shows 1,000.
   4. Create a GitHub repo `glowcue` (public, empty, no README yet).
   5. Create Render and Vercel accounts (GitHub sign-in).
   6. **Create the Devpost project draft now** and note every form field (the form is behind login and can't be verified from here).
   7. Run the trademark / handle check ([§3](PRODUCT_BRIEF.md)).
   8. Take 2–3 test selfies per [§6.1](YOUCAM_API.md) specs.
   9. Answer the decisions in [§20](USER_CHECKLIST.md)-F.
   10. Install Playwright browsers later (Claude Code will do it).
4. **Tools:** browser, password manager, phone camera.
5. **Accounts:** Devpost, YouCam console, GitHub, Render, Vercel, YouTube (Google).
6. **Outputs:** API key stored; balance confirmed; repo URL; Devpost draft; decisions answered.
7. **Dependencies:** none.
8. **Difficulties:** redeem-code email delay or failure → forum post plus email `contact_event@PerfectCorp.com` with your User ID. **Meanwhile, build in mock mode** using the documented SD sample JSON as a provisional fixture.
9. **Verification:** console shows 1,000 units; Playground loads.
10. **Hours:** 1.5.
11. **Acceptance:** key in hand **or** a support ticket sent and mock-mode work started.
12. **Next:** Phase 2 (the live probe) runs while Claude Code does Phase 1/3 docs.

Installed already **[V]**: Python 3.14.6, Node 24.17, npm 11.13, Git 2.54. `gh` CLI is not installed; it's optional.

### PHASE 1: Product definition (Sat 18:00–18:30, 0.5 h)
- **Objective:** freeze the PRD ([§5](PRD.md)) into `docs/`.
- **Actions:** Claude Code copies this blueprint into `docs/BLUEPRINT.md` and writes `DECISIONS.md` with your answers and `PROGRESS.md` with the checklist.
- **Outputs:** the docs folder.
- **Verification:** you skim it and approve.
- **Acceptance:** MVP list frozen; any later addition needs a DECISIONS entry.
- **Next:** Phase 2.

### PHASE 2: YouCam API verification (Sat 18:00–19:30, 1.5 h; overlaps Phase 1)
- **Objective:** one real, controlled run; resolve every [U] in [§6](YOUCAM_API.md).
- **Actions:**
  1. Free calls: credit + feature-cost.
  2. Playground run, SD, with our 10 actions (14 units).
  3. Claude Code writes `scripts/probe_youcam.py`. **You run it once** with your selfie. It does file → PUT → task → poll → saves the raw JSON + masks → calls `task/delete` and records whether it succeeds and whether units are deducted.
  4. Inspect: `skin_type` shape, `region` presence, mask format and dimensions vs the input, processing time.
  5. Write findings to `docs/YOUCAM_NOTES.md`.
  6. Produce the sanitised fixture.
- **Tools:** Claude Code, terminal, the console usage page.
- **Difficulties:** `error_src_face_too_small` → crop closer; 401 → re-copy the key, check the space after "Bearer".
- **Verification:** the balance drops by exactly 14 per success; the masks overlay correctly in a quick HTML test page.
- **Hours:** 1.5. **Units:** ≤ 42.
- **Acceptance:** fixture committed (sanitised); all [U] resolved or work-arounds chosen.
- **Next:** Phase 3.

### PHASE 3: Architecture preparation (Sat 19:30–20:00, 0.5 h)
- **Objective:** scaffolds, models and contracts fixed in code.
- **Outputs:** repo skeleton ([§7.6](ARCHITECTURE.md)), `models.py`, `types.ts`, `.env.example` files, `ARCHITECTURE.md`, first commit.
- **Acceptance:** `uvicorn` starts and serves `/api/health`; `npm run dev` shows a placeholder; CI-free local tests run.
- **Next:** Phase 4.

### PHASE 4: Backend implementation (Sat 20:00–00:30 + Sun 07:00–08:00, 5.5 h)

| Task | Produces | Done when |
|---|---|---|
| 4-A Config | `config.py` (YOUCAM_MODE, YOUCAM_API_KEY, LIVE_ANALYSIS_ENABLED, MAX_LIVE_PER_DAY, PER_IP_PER_DAY, CREDIT_FLOOR, FRONTEND_ORIGIN, CURRENCY) | Missing key in live mode → clear startup error |
| 4-B YouCam client | `youcam_client.py` with typed errors, backoff | Unit tests with a fake HTTP transport (`httpx.MockTransport`) |
| 4-C Image validation | Pillow checks, re-encode, metadata strip | Tests: png/jpg ok, gif rejected, 300 px rejected, > 10 MB rejected, EXIF gone |
| 4-D Normaliser | `normalize.py` | Tests against the real fixture and edge cases (missing type, unknown type, `dark_circle_v2` mapping) |
| 4-E Catalogue | `catalogue.json` + loader + validator | Tests: 15 unique ids, enums valid, banned words absent |
| 4-F Engine | concerns / scoring / optimiser / explain | ≥ 15 tests including all [§9.4](RECOMMENDATION_ENGINE.md) edge cases; deterministic |
| 4-G Routine | `routine.py` | Tests: SPF last AM; vitamin C not PM; retinol + AHA alternate |
| 4-H Routes | analyses (create / poll / sample), catalogue, recommendations, cart quote, limits | TestClient tests for each, in mock mode |
| 4-I Errors | uniform `{error:{code,message,retryable}}` | Each YouCam error code mapped |

**Hours:** 5.5. **Acceptance:** `pytest` green; the full API works in mock mode via `/docs`.

### PHASE 5: Frontend implementation (Sun 08:00–17:30, ~8.5 h with breaks)
**Build order (each step commits):**
1. Design system: tokens, fonts, Button, Card, Badge, ScoreBar, Stepper, Disclaimer (1 h).
2. Landing (0.75 h).
3. Analyse page: imagePrep, consent (1.25 h).
4. Processing + polling (0.5 h).
5. Results + HeatmapViewer (1.5 h).
6. Routine page with preferences, timeline, ProductCard, receipts, BudgetMeter (2 h).
7. Product drawer + Swap (0.5 h).
8. Cart + Checkout preview (0.75 h).
9. Responsive pass (0.5 h).

**Acceptance:** the whole journey works in mock mode at 375 px and 1280 px.

### PHASE 6: Integration (Sun 17:30–19:30, 2 h)
- **Objective:** live mode end to end locally.
- **Actions:** point the frontend at the local backend in live mode → run 1–2 real analyses (≤ 28 units) → fix mask alignment and error mapping → add the Playwright smoke test (mock mode) → commit.
- **Data flow:** blob → multipart → 202 id → poll → result in SessionContext → POST recommendations on Routine mount and on pref change → cart quote.
- **Acceptance:** a real selfie reaches checkout with no console errors; every YouCam error path shows its UI state, tested with deliberately bad images (tiny, no face, dark).

### PHASE 7: Refinement (Sun 21:00–23:00, 2 h)
Priorities, ranked by judging value:
1. Receipt copy quality and the honest-score explainer (Idea / Impact).
2. Visual polish of Results and Routine (Design).
3. Empty, error and loading states (Design).
4. Accessibility: keyboard, contrast, aria-live.
5. Micro-animations.

Antigravity runs a full visual / UX sweep first, and Claude Code fixes from its report. **Feature freeze at 21:00.**

### PHASE 8: Quality assurance (runs through 4–7; final pass Mon 06:30–07:30). See [§13](TEST_PLAN.md).

### PHASE 9: Deployment (Sun 19:30–21:00, 1.5 h)
**Deploy before polishing.** See [§14](DEPLOYMENT.md). **Acceptance:** the public URL completes the sample flow on your phone over mobile data, and one live analysis succeeds in production.

### PHASE 10: GitHub & documentation (Mon 06:30–08:00, 1.5 h). See [§15](SUBMISSION_CHECKLIST.md).

### PHASE 11: Screenshots & demo video (Mon 08:00–10:30, 2.5 h). See [§16](submission/DEMO_STORYBOARD.md).

### PHASE 12: Devpost submission (Mon 10:30–12:00, 1.5 h). See [§17](submission/DEVPOST_DRAFT.md). **Save the draft repeatedly.**

### PHASE 13: Final review & submit (Mon 12:00–14:00)
Run the compliance checklist ([§21](SUBMISSION_CHECKLIST.md)) and **click Submit by 14:00 WAT**. Keep 14:00–17:45 (**3 h 45 min**) as contingency, using it only for fixes. Re-open the submission to confirm it shows "Submitted". Devpost lets you edit until the deadline.

---

## 18. Detailed development timeline (WAT)

| Milestone | Start | Duration | Output | Completion criteria | Contingency |
|---|---|---|---|---|---|
| M0 Accounts & key | Sat 16:30 | 1.5 h | Key, repo, draft, decisions | Balance 1,000 visible | If the code fails: mock-mode build continues; escalate by email |
| M1 Docs + scaffold (P1–P2) | Sat 18:00 | 1.5 h | Repo skeleton, docs | Health endpoint works | — |
| M2 Live probe + fixture (P3 probe, P4) | Sat 18:30 | 1.5 h | Fixture, YOUCAM_NOTES | All [U] resolved | Use the documented sample JSON as the provisional fixture |
| M3 Catalogue + engine + routine (P5–P7) | Sat 20:00 | 4.5 h | Tested engine | pytest green | Drop alternatives (F9) if late |
| Sleep | Sat 00:30 | 6 h | — | — | — |
| M4 Backend routes finish (P3 routes) | Sun 07:00 | 1 h | API complete in mock | Route tests green | — |
| M5 Frontend core (P8–P11) | Sun 08:00 | 5 h | Landing → Results | Mock journey to Results | Simplify heatmap to a single overlay toggle |
| Break | Sun 13:00 | 0.75 h | — | — | — |
| M6 Frontend commerce (P12–P13) | Sun 13:45 | 3.75 h | Routine, Cart, Checkout | Mock journey complete | Cut the product drawer to inline details |
| M7 Integration live (P14) | Sun 17:30 | 2 h | Live journey | Real selfie → checkout | — |
| **M8 Deploy (P17)** | Sun 19:30 | 1.5 h | Public URLs | Phone test passes | Fallback: single Render service |
| **Feature freeze** | Sun 21:00 | — | — | — | — |
| M9 Refine + QA (Antigravity, P15–P16) | Sun 21:00 | 2 h | Fixes | No P0/P1 | — |
| Sleep | Sun 23:00 | 7 h | — | — | — |
| M10 Final QA + docs (P18) | Mon 06:30 | 1.5 h | README | Fresh-clone test passes | — |
| M11 Screenshots + video (P19–P20) | Mon 08:00 | 2.5 h | YouTube link | Public, ≤ 3 min | Shorter, single-take video |
| M12 Devpost (P21) | Mon 10:30 | 1.5 h | Complete draft | All fields filled | — |
| M13 Final check + **SUBMIT** | Mon 12:00 | 2 h | Submitted | Status "Submitted" | — |
| Contingency | Mon 14:00 | 3 h 45 min | — | — | Only critical fixes |

**Critical path:** API key → probe/fixture → engine → Results/Routine UI → integration → deploy → video → submit.
**Parallelisable:** you handle accounts and selfies while Claude Code scaffolds; Antigravity reviews while Claude Code writes tests; you draft Devpost text while the video renders.
**Bottlenecks:** your availability to answer prompts and run live calls; video recording.
**Cut order if late:** product drawer → swap alternatives → mobile camera capture (keep file upload) → per-concern heatmap chips (keep one overlay) → Vitest. **Never cut:** live YouCam integration, sample mode, routine + cart, README, video.

---

## 19. Risk register

| # | Risk | Impact | Likelihood | Prevention | Contingency |
|---|---|---|---|---|---|
| 1 | **Time shortage** | Incomplete submission | **High** | Fixed schedule, feature freeze Sun 21:00, cut list | Submit the MVP with sample mode; partial features hidden |
| 2 | API authentication / redeem failure | Blocks live analysis | Medium (forum shows past issues) | Redeem in Phase 0; test the free credit endpoint | Build in mock mode with the documented sample JSON; email support; the live call can happen as late as Sunday |
| 3 | Deployment failure / cold start | No public app / bad judge experience | Medium | Deploy Sunday 19:30; warm-up ping | Single-service Render fallback; Netlify; local-run instructions in the README |
| 4 | Mask misalignment or unexpected format | Weak visuals | Medium | Pre-resize ≤ 2048; verify in Phase 2 | Use `enable_mask_overlay:true` single blended JPG per run; or text-only "where it shows up" |
| 5 | Incorrect API interpretation | Wrong recommendations | Low (docs explicit) | Use `raw_score`, higher = better, tested | Fix the mapping in one function (normaliser) |
| 6 | Quota exhaustion (public abuse) | Blocks final verification | Medium | Per-IP / day + global caps, credit floor 100, kill switch | Sample mode; social-sharing bonus (+500 / platform) |
| 7 | Integration failure | Broken journey | Medium | Contracts typed on both sides; mock-first | Hard-code the sample path for the demo |
| 8 | Photo or API-key exposure | Security incident, disqualification risk | Low | Key only in Render env; `.gitignore`; push protection; no logs | Rotate the key immediately in the console |
| 9 | Inaccurate product information | Credibility | Low (fictional) | Labelled demo catalogue; cosmetic copy; banned-word test | Remove the offending claim |
| 10 | Brand-name conflict | Rebrand | Low | [§3](PRODUCT_BRIEF.md) check | Backup names; the name is in few places (config constant) |
| 11 | Third-party trademark in the video | Rules breach | Low | Fictional brand; no logos except the YouCam API name | Re-record the segment |
| 12 | Medical-claim perception | Judge or ethics concern | Low | Disclaimers; banned words; "cosmetic" framing | Copy fix |
| 13 | Score bias across skin tones | Unfair results for the target audience | Unknown **[U]** | State the limitation honestly; no absolute thresholds headlined | Present as a roadmap item (validation study) |
| 14 | Python 3.14 package incompatibility | Setup delay | Low–Med | Pin versions | Install Python 3.12 |
| 15 | App down during judging (to 20 Nov) | Lower scores | Medium | Freeze `main`; weekly check | Judges may score on video + description (rules allow it) |
| 16 | Devpost form surprises (e.g. school email) | Missed award | Low | Open the draft in Phase 0 | — |

**Critical:** 1, 2, 3. **Watch:** 4, 6, 7, 15.

---
