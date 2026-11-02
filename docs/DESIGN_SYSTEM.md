# Design System & Screen Specification

> **Status:** planned design from the GlowCue blueprint (research snapshot 31 Oct 2026). Nothing here is implemented unless [PROJECT_STATUS](PROJECT_STATUS.md) says so. Tags: **[V]** verified, **[A]** assumption, **[R]** recommendation, **[U]** unresolved.

## 8. Screen-by-screen design specification

### 8.1 Visual direction
- **Palette (tokens):**
  - `--bg` #F7F3EE (warm ivory)
  - `--surface` #FFFFFF
  - `--ink` #1F1D1B (charcoal)
  - `--muted` #6B645C
  - `--sage` #5E7A64 (primary)
  - `--sage-soft` #E4EBE3
  - `--clay` #C47F5A (accent / priority)
  - `--line` #E7E0D7

  Avoid neon gradients. (No heatmap overlay is implemented; YouCam masks are not used.)
- **Type:** Fraunces 600 for headings (36/28/22), Inter 400/500 for body (16/14). 1.5 line-height.
- **Shape and space:** 16 px radius cards, soft 1 px borders rather than heavy shadows, 8-pt spacing grid, max-width 1120 px.
- **Motion:** 150–250 ms fades and slides; respect `prefers-reduced-motion`.
- **Tone:** warm, plain-English, never alarmist ("more visible", "a closer look", never "bad skin").

### 8.2 Flow organisation
A **linear stepper** (Analyse → Results → Routine → Cart) with a persistent cart icon. No sidebar or tabs. Morning and Evening are a toggle *inside* Routine. Product detail is a drawer. Preferences sit at the top of Routine as a collapsible panel, so changing the budget instantly recomputes. That gives **8 routes** for 13 screen concepts.

### 8.3 Screens

| Screen | Purpose | Layout & components | Interactions | Responsive | Loading / error |
|---|---|---|---|---|---|
| **Landing** `/` | Hook and trust | Hero (headline "Know your skin. Choose with confidence.", sub "The smallest routine that covers your skin, within your budget."), two CTAs (**Analyse my selfie**, **Try a recorded sample**), 3-step strip, "Powered by YouCam AI Skin Analysis" text credit, privacy and not-medical notes, footer | CTAs; fires the `/api/health` warm-up | Stacked hero on mobile | If health fails after 20 s: "Server waking up…" with retry; the sample CTA still visible |
| **Analyse** `/analyze` | Consent + capture | Photo tips (good light, face fills frame, hair off forehead, no glasses or makeup), dropzone / camera button, preview with guide oval, consent checkbox + privacy summary, Analyse button | Pick or take photo → client validation → preview → consent → submit | Camera button prominent on mobile | Inline errors: type, size, too small. Button disabled until valid and consented. |
| **Processing** `/processing/:id` | Wait honestly | Calm animation, staged text ("Uploading securely", "YouCam is analysing 10 skin attributes", "Preparing your results"), cancel link | Polls every 2 s, timeout 90 s | — | Errors mapped to friendly copy + "Try another photo" / "Use sample instead" |
| **Results** `/results` | Understand | (a) "Your top 3 priorities" cards (concern, plain explanation, band chip); (b) HeatmapViewer (**not implemented**: the report shows scores only); (c) all-metrics list with score bars; (d) skin type; (e) "About these scores" accordion (raw vs ui score honesty note, no confidence values, cosmetic only); CTA "Build my routine" | Chip click highlights the metric row | Mobile: priorities first | Missing score → shown as not measured. Demo badge on demo results. |
| **Routine** `/routine` | Decide | Preferences panel (budget slider with currency, "I already own" chips, fragrance-free, sensitive, routine size); summary bar (coverage %, product count, total vs budget); AM/PM toggle → **RoutineTimeline** steps; each step a ProductCard (image, name, price, key ingredient, "Why this?" receipts, Swap, Details drawer); warnings (e.g. "Sunscreen is essential; you said you own one"); unaddressed concerns note; CTA **Add routine to cart** | Any preference change → POST recommendations (debounced 300 ms) | Single column on mobile; sticky summary bar at the bottom | Skeleton cards; infeasible budget → banner with "Increase to ₦X" quick action |
| **Product drawer** | Detail | Image, description, full ingredient list, how to use, AM/PM, cautions, demo-product label, price, receipts | Close, Swap | Full-screen sheet on mobile | — |
| **Cart** `/cart` | Purchase intent | Line items (qty steppers, remove), subtotal from server quote, budget meter, "Routine complete ✓" indicator, CTA **Preview checkout** | Qty / remove → re-quote | — | Empty state → "Build your routine" |
| **Checkout preview** `/checkout` | Close the loop | Order summary, the routine card in printable form, "Demo store — no payment is taken", **Start over & clear my data** | Clear → wipes context and sessionStorage → Landing | — | — |
| **Not found / error** | Recovery | Friendly message + home link | — | — | — |

### 8.4 Visual assets

| Asset | Source [R] | Who |
|---|---|---|
| Logo / wordmark + favicon | SVG wordmark "GlowCue" in Fraunces with a small sage "cue" dot | Claude Code generates the SVG; you approve |
| Product images (15) | **Consistent flat SVG packshots** (bottle, tube, jar, dropper silhouettes, colour-coded by category, label "GlowCue Demo") | Claude Code generates them; no copyright or trademark risk |
| Icons | Lucide React (ISC licence) | Claude Code |
| Fonts | Google Fonts Fraunces + Inter (OFL) | Claude Code |
| Sample photo for sample mode | **Your own selfie, or a consenting friend's with written consent**, taken per the YouCam tips (see decision [§20-F3](USER_CHECKLIST.md)). Do **not** use stock or celebrity photos: their licences rarely cover biometric analysis or publication of scores. | **You** |
| OG / social image | Generated from a screenshot | Claude Code |
| Background | Plain warm ivory, optional subtle grain via CSS. No stock imagery needed. | Claude Code |

---
