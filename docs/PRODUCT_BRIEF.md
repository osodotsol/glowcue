# Product Brief

> **Status:** planned design from the GlowCue blueprint (research snapshot 31 Oct 2026). Nothing here is implemented unless [PROJECT_STATUS](PROJECT_STATUS.md) says so. Tags: **[V]** verified, **[A]** assumption, **[R]** recommendation, **[U]** unresolved.

## 1. Executive assessment

**Verdict: build GlowCue, but sharpen it.** A plain "selfie → scores → product list" app would not stand out, for three reasons.

1. **Perfect Corp already sells that exact product.** Its own AI Skin Analysis plus Auto Product Recommendation tool is deployed with retailers ([Business Wire, 2024](https://www.businesswire.com/news/home/20240919987698/en/Perfect-Corp.-Introduces-Auto-Product-Recommendation-Tool-for-Skincare-Brands-and-Retailers-Powered-by-AI)). The v2.1 Skin Analysis API even mentions an optional built-in "Product Recommendation / Advanced Skin Report" output ([API reference](https://docs.perfectcorp.com/reference/ai_skin_analysis.md)) **[V]**. The judges are Perfect Corp staff, so they know this well.
2. **"Quality of Idea" is a quarter of the score**, and it explicitly asks for a *"creative, non-obvious use"* of the API **[V]** ([Rules [§6](YOUCAM_API.md)](https://youcam-api-skin-ai-ecommerce.devpost.com/rules)).
3. **Round-one winners all took non-obvious angles** **[V]** ([gallery](https://youcam-api.devpost.com/project-gallery)):
   - Aloud (1st): beauty AI that blind shoppers can use alone.
   - ShadeSpan (2nd): every garment shown on every skin tone.
   - CASTING, KeepMe and ConfidFit: inclusivity, trust in try-on, and merchant tooling.

   Several generic "skin → routine" entries (Atelier, Wabi-Sabi, Skin Journey, GlowCycle) did not place.

**The sharpened concept [R]: "The smallest routine that covers your skin, within your budget, without buying what you already own."**

GlowCue keeps your journey intact but makes four things its core:

| Differentiator | What it means | Why judges should care |
|---|---|---|
| **Coverage-per-budget optimiser** | Instead of listing products, GlowCue computes the *fewest* products that cover your measured priorities within a budget. It tests every valid combination and shows a "coverage score". | It is a real algorithm, not an API wrapper (Technological Implementation), and it gives retailers a trust-building alternative to upselling. |
| **Shelf check** | "I already own a cleanser / moisturiser / sunscreen." GlowCue skips those and spends the budget on gaps. | It is a non-obvious e-commerce angle: it reduces over-buying and returns, and builds trust. |
| **Honest-score transparency** | YouCam's docs state that `ui_score` is deliberately inflated as a "psychological motivator" **[V]**. GlowCue ranks concerns on `raw_score` and explains this. | It shows "genuine understanding of the problem space", which the judging criteria name explicitly. |
| **Receipts for every product** | Each pick traces measured metric → concern → ingredient → product → routine slot. | It delivers the explainability you asked for and is clearly demoable. |

**Positioning (provisionally ADOPTED as default, see [ADR-003](decisions/ADR-003-product-catalogue.md)); originally flagged as a decision ([§20-F1](USER_CHECKLIST.md)):** position GlowCue for **budget-conscious first-time skincare shoppers, launching with young Nigerian shoppers**. That means NGN pricing and a **"no-bleach promise"**: the catalogue never admits skin-lightening or bleaching agents, and pigmentation concerns are answered with sunscreen plus gentle tone-evening ingredients. This is credible and specific. A WHO Africa fact sheet (2023) lists Nigeria at 77% skin-lightening product use among women and highlights mercury risk ([WHO AFRO fact sheet](https://files.aho.afro.who.int/afahobckpcontainer/production/files/Skin_Bleaching_in_Africa_regional_fact_sheet_Nov23.pdf)) **[V]**. The figure dates from a 2011 survey, so cite it with its date.

**Feasibility:** you have about 45 working-clock hours, and realistically about 30 hours of focused work after sleep. With Claude Code doing most of the implementation, an MVP of the full journey is achievable **if** we:
- deploy early (Sunday evening);
- build against a recorded fixture after a single live API call; and
- stop adding features at Sunday 21:00.

**Biggest risks, in order:**
1. Time.
2. Redeem code or API key problems. Do this first.
3. Deployment surprises. Deploy on Sunday, not Monday.
4. Mask-overlay alignment.

---

## 3. Brand-name assessment

| Check | Finding | Status |
|---|---|---|
| Exact-name skincare product or app | Web searches for "GlowCue" (skincare, app, brand) found **no product or company using it**. | [V] (web only) |
| Similar names | **Crowded "Glow-" space:** Glow Recipe (brand), Glow Hub (UK brand), "Glow – AI Beauty Coach" (app), Glow Me, Glowcode, GlowDNA, and **GlowCycle (a round-one entry in this hackathon series)**. None is an exact match. | [V] |
| glowcue.com | **Taken.** Recently registered at Namecheap and parked. | [V] |
| glowcue.app / .co / .io | No DNS records. This *suggests* they're unregistered but doesn't prove it. Check at a registrar. | [U] |
| GitHub `github.com/glowcue` | Returns 404, so the org/user name looks free. A repo called `glowcue` under your account is fine either way. | [V] |
| Trademark | Not checked. USPTO and WIPO search pages are dynamic. **No legal clearance is implied.** | [U] |

**Recommendation [R]: keep "GlowCue".** There is no direct material collision. "Glow" is generic in beauty, and "Cue" makes the combination distinctive. The parked .com doesn't matter for a hackathon; host on a free subdomain.

**Five-minute action for you** (Phase 0): search "GlowCue" on [WIPO Global Brand Database](https://branddb.wipo.int/) and [USPTO Trademark Search](https://tmsearch.uspto.gov/), plus Instagram, X and TikTok handles. If an exact live mark appears in Nice class 3 (cosmetics) or class 9/42 (software), tell me before Phase 10. Backup names, all unverified: **CueSkin**, **Skinwise Cart**, **RoutineCue**.

---

## 4. Product evaluation and improvements

### 4.1 Competitive landscape

| Category | Examples | What they do well | Gap GlowCue targets |
|---|---|---|---|
| Brand / retailer skin analysers (often Perfect Corp-powered) | Perfect Corp Skincare Pro deployments (Douglas, BENU pharmacies, Cetaphil) | Accurate analysis, branded catalogues | **Single-brand bias.** They recommend *more* of their own range. No budget optimisation; nothing about what you already own. |
| Consumer AI skin apps | Glow AI, Glow Me, TroveSkin and similar | Coaching, tracking | Subscriptions, generic advice, weak commerce link, opaque "why" |
| Ingredient checkers | INCIdecoder, Skincarisma, Yuka | Ingredient transparency | No analysis of *your* skin, no routine assembly or budget |
| Round-one entries | Atelier, Wabi-Sabi, Skin Journey, BaddieGuide, GlowCycle | Various "skin → routine" flows | Most show lists. Few optimise for cost, coverage or what you own. |

**Is GlowCue original?** The base concept (analysis → recommendations) is **not** original. The **budget-coverage optimiser plus shelf check plus honest-score explanation** combination is uncommon. I found no direct equivalent, but I can't claim uniqueness **[A]**.

### 4.2 Feature classification

| Feature | Class | Reason |
|---|---|---|
| Upload + consent + client-side resize / EXIF strip | **MVP essential** | Core flow and privacy |
| Live YouCam SD analysis (10 concerns) | **MVP essential** | Stage-1 pass condition |
| Recorded-sample mode (clearly labelled real recorded result) | **MVP essential** | Organiser-approved judge access; protects credits |
| Results with priority ranking on `raw_score` and honest-score note | **MVP essential** | Core of differentiation |
| Heatmap viewer (official masks, per-concern toggle, opacity) | **MVP essential** | Strong visual, verified API output |
| Preferences: budget, fragrance-free, sensitive skin, routine size | **MVP essential** | Needed for the optimiser |
| Shelf check ("I already own…") | **MVP essential (lite)** | Cheap to build: it removes categories. Key differentiator. |
| Coverage-per-budget optimiser | **MVP essential** | Key differentiator |
| Explainable "receipt" per product | **MVP essential** | Key differentiator |
| AM / PM routine with ordering and conflict rules | **MVP essential** | Requested; demoable |
| Cart + total + budget meter + checkout preview (no payment) | **MVP essential** | eCommerce value |
| Swap to alternative product (re-quotes the total) | Valuable enhancement | Build if on schedule by Sun 17:30 |
| Product detail drawer | Valuable enhancement | A simple drawer is enough |
| Delete YouCam task + inputs after results | Valuable enhancement → **promote if the endpoint verifies** | Strong privacy story |
| NGN / USD currency switch | Optional | Pick one currency instead |
| Skin-age display | **Exclude** | Sensitive and adds little; the API returns it but we hide it |
| Progress tracking over time, accounts, DB | **Exclude** | Needs storage and auth; privacy burden |
| LLM chatbot / YouCam "Advanced Skin Report" | **Exclude** | Parameters undocumented; contradicts the deterministic and explainable promise; you asked for no chatbot |
| Makeup / foundation VTO | Optional (post-hackathon) | Real extra value but extra API and UI risk |
| Real payment | **Exclude** | Out of scope |

---
