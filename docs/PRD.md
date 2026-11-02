# Product Requirements Document

> **Status:** planned design from the GlowCue blueprint (research snapshot 31 Oct 2026). Nothing here is implemented unless [PROJECT_STATUS](PROJECT_STATUS.md) says so. Tags: **[V]** verified, **[A]** assumption, **[R]** recommendation, **[U]** unresolved.

## 5. Product Requirements Document (PRD)

### 5.1 Objectives
1. Turn one selfie into a ranked, plain-language view of cosmetic skin priorities, using YouCam Skin Analysis.
2. Produce the **smallest, budget-fitting, conflict-free AM/PM routine** that covers those priorities, excluding products the user already owns.
3. Explain every recommendation with a traceable receipt.
4. Move the user to a filled cart with a transparent total in **≤ 3 minutes** from landing.
5. Never retain the user's photo. Make no medical claims.

### 5.2 Target user
**Primary:** an 18–30-year-old first-time or budget-constrained skincare shopper. They are overwhelmed by choice, afraid of wasting money, and unsure what to buy first or whether they need it. *Purchasing problem:* "I have ₦X to spend. What should I buy, in what order, and what can I skip?"
**Secondary (retailer value):** an online beauty retailer that wants higher-trust conversion and fewer returns from mismatched purchases.

### 5.3 Core use cases
- UC1: Analyse my skin from a selfie, or try the recorded sample.
- UC2: Understand my top priorities. *(Planned: see where they show up on a heatmap. **Not implemented:** the report shows scores only.)*
- UC3: Set budget and preferences, and tell GlowCue what I already own.
- UC4: Get a minimal AM/PM routine with reasons and a total.
- UC5: Swap a product and see the total update.
- UC6: Add the whole routine to the cart and preview checkout.

### 5.4 Customer journey
Landing → (Try sample *(not built)* | Analyse my selfie) → Consent + upload → Processing (≈10–40 s **[A]**) → Results (priorities + scores) → Preferences (budget, own-already, fragrance-free, sensitive, routine size) → Your routine (AM / PM, receipts, coverage, total) → Cart → Checkout preview → "Start over / delete my session".

*As built (1 Nov 2026): the consultation comes before the selfie, and analysis is either a labelled demo profile or a consented live YouCam analysis. The sample mode and heatmap were not built; see the [README](../README.md).*

### 5.5 Functional requirements

| ID | Feature | Purpose | Interaction / Inputs | Outputs | Backend | Frontend | Errors | Acceptance criteria |
|---|---|---|---|---|---|---|---|---|
| F1 | Landing | Explain value, start the flow | CTA buttons | — | `GET /api/health` warm-up, `GET /api/config` | Hero, 3-step explainer, disclaimer, CTAs | Backend asleep → show "waking server" gracefully | Loads < 2 s on 4G; both CTAs work; disclaimer visible |
| F2 | Consent + upload | Lawful, informed processing | Checkbox (required), file input / camera (`capture="user"`), photo tips | Resized JPEG blob | Validates consent flag, type, size, dimensions with Pillow; strips metadata | Validate jpg/png < 10 MB, short side ≥ 480 px; downscale long side to ≤ 2048 px; re-encode (strips EXIF and GPS) | Wrong type, too small, too large, no consent | Can't submit without consent; invalid files are rejected with a friendly message; EXIF absent in the uploaded blob |
| F3 | Analysis (live) | Run YouCam | Image + consent | `analysis_id` | File API → PUT → task → poll → normalise → (optionally) delete task | Progress screen with honest staged messages; polls every 2 s | YouCam errors (`error_no_face`, `error_src_face_too_small`, `error_lighting_dark`, `CreditInsufficiency`, 429, timeout) map to friendly retry guidance | Real result displayed for a good selfie; every listed error shows a specific message; no key in browser |
| F4 | Sample mode (**not implemented**; labelled demo profiles are used instead, [ADR-005](decisions/ADR-005-demo-provider-and-redesign.md)) | Judge access and credit saving | "Try recorded sample" | Recorded normalised result plus mask assets | Serves fixture | Badge "Recorded real YouCam result — sample photo" | — | Works with live mode disabled; always labelled |
| F5 | Results | Understand priorities | — | Top 3 priorities, all metrics, skin type | — | Priority cards, metric list with bands, honest-score explainer, "not measured" states | Metric missing → "not measured" | Ranking uses `raw_score`; bands follow [§9](RECOMMENDATION_ENGINE.md); disclaimer present |
| F6 | Heatmaps (**not implemented**; YouCam masks are not requested and the report shows scores only) | Visual explanation | Toggle a concern, opacity slider | Overlay | Supplies masks (data URLs or URLs) | Stack mask PNGs over the photo with identical box sizing | Mask missing → "no map for this concern" | Masks align within visual tolerance on desktop and mobile; legend explains it's YouCam's detection map |
| F7 | Preferences | Constrain the optimiser | Budget slider, own-already checkboxes, fragrance-free, sensitive, routine size (Minimal ≤ 3 / Balanced ≤ 5 / Complete ≤ 7) | Preference object | Validates | Form with sensible defaults | Budget below the cheapest core routine → warning | Changing any field re-runs recommendations in < 1 s |
| F8 | Recommendations + routine | Core value | Metrics + preferences | Selected products, AM/PM steps, receipts, coverage %, total, budget status, warnings | Deterministic engine ([§9](RECOMMENDATION_ENGINE.md)) | Routine timeline, product cards with "Why this?" receipts | Infeasible budget → best partial routine + "₦X over" + suggestions | Same input gives the same output; every product has ≥ 1 receipt tied to a measured metric; no conflicting actives on the same night; sunscreen in AM unless owned |
| F9 | Swap alternative | Choice | "Swap" on a card | New product, re-quoted total | `alternatives` precomputed per slot | Drawer of ≤ 3 alternatives | None suitable → hide swap | Total and coverage update correctly |
| F10 | Cart | Purchase intent | "Add routine to cart", qty, remove | Line items, subtotal | `POST /api/cart/quote` recomputes prices server-side | Cart page, budget meter | Unknown product id → 400 | Totals are correct (unit test); cart survives navigation (sessionStorage, no images) |
| F11 | Checkout preview | Close the loop | — | Order summary | — | Summary, "Demo store: no payment taken", "Start over & clear data" | — | No payment fields; clear-data wipes state |

### 5.6 Non-functional requirements
- **Performance:** first load < 2 s with a warm backend; analysis ≤ 60 s end to end with a 90 s timeout; recommendation < 300 ms server time.
- **Reliability:** sample mode works even if YouCam or credits fail; the kill switch `LIVE_ANALYSIS_ENABLED=false` falls back to it.
- **Security:**
  - The API key lives only in backend env vars.
  - CORS allows only the frontend origin.
  - Upload size cap of 10 MB.
  - Per-IP limit of 5 live analyses per day, plus a global daily cap (`MAX_LIVE_PER_DAY`, default 25).
  - No user-supplied URLs are fetched (no SSRF).
- **Privacy:**
  - Images are processed in memory only, never written to disk or logged.
  - EXIF is stripped on both client and server.
  - Results are held in memory with a 30-minute TTL.
  - The YouCam task and its files are deleted after retrieval if the endpoint verifies; otherwise state YouCam's 30-day auto-deletion **[V]** ([retention](https://docs.perfectcorp.com/develop/file_retention_period.md)).
  - Privacy notice on the consent screen.
- **Accessibility:** WCAG 2.1 AA contrast, keyboard navigation, alt text, `aria-live` for progress, and information never given by colour alone (if heatmaps are ever added, their content must also be given as text).
- **Responsiveness:** 360 px → 1440 px, mobile-first.
- **Maintainability:** typed models (Pydantic, TypeScript), catalogue as validated JSON, the engine as pure functions with ≥ 90% unit-test coverage.

### 5.7 MVP scope
In scope: F1–F8, F10, F11, plus F9 if on schedule. Out of scope: accounts, DB, payments, progress tracking, LLM, VTO, multi-language.

### 5.8 Definition of done (per feature)
1. Acceptance criteria above pass.
2. Tests written and green (backend pytest; e2e smoke in mock mode).
3. Works at 375 px and 1280 px.
4. Antigravity visual check logged.
5. Committed with a descriptive message.
6. No console errors.

---
