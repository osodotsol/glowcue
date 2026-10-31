# Recommendation Engine

> **Status:** planned design from the GlowCue blueprint (research snapshot 31 Oct 2026). Nothing here is implemented unless [PROJECT_STATUS](PROJECT_STATUS.md) says so. Tags: **[V]** verified, **[A]** assumption, **[R]** recommendation, **[U]** unresolved.

## 9. Product catalogue & recommendation engine

### 9.1 Real or fictional products? [R] **Fictional demo products, clearly labelled.**
- The video rules forbid **third-party trademarks** without permission **[V]**, so real brand names and packshots on screen are a risk.
- Verifying current real prices, availability and INCI lists for 15 products in Nigeria within 45 h is not feasible, and you asked us not to invent claims.
- Fictional products can use **real, well-known cosmetic ingredients** at typical concentrations, with claims phrased cosmetically ("helps the look of…").
- Every product card and the README say: **"Demo catalogue: fictional products for illustration. Prices are illustrative."**
- Post-hackathon, the catalogue schema is ready for a real retailer feed.

**Schema (each product)**

```json
{
  "id": "gc-cln-02",
  "name": "Balancing Gel Cleanser",
  "brand": "GlowCue Demo",
  "category": "cleanser",               // cleanser|toner_exfoliant|serum|eye|moisturiser|sunscreen
  "description": "Low-foam gel cleanser for shine-prone skin.",
  "key_ingredients": ["salicylic acid 0.5%", "niacinamide"],
  "ingredients_inci": "Aqua, ..., Salicylic Acid, Niacinamide, ...",   // illustrative, marked as such
  "targets": {"oiliness": 0.8, "pore": 0.6, "acne": 0.6},             // 0–1 strength per concern
  "skin_types": ["oily", "combination", "normal"],
  "time_of_day": ["am", "pm"],
  "frequency": "daily",
  "usage": "Massage onto damp skin for 30 seconds, rinse.",
  "actives": ["bha"],                   // used for conflict rules
  "fragrance_free": true,
  "sensitive_ok": false,
  "cautions": ["May feel drying if overused."],
  "price": 6500, "currency": "NGN",
  "image": "/products/gc-cln-02.svg",
  "source": "fictional_demo",
  "rank_bias": 0                        // tie-breaker metadata
}
```

**Proposed 15 products** (prices illustrative; final in Phase 4-E):

| # | Name | Cat | Key ingredients | Targets | AM/PM | Notes |
|---|---|---|---|---|---|---|
| 1 | Gentle Cream Cleanser | cleanser | glycerin, ceramides | moisture, redness | AM/PM | sensitive_ok, fragrance-free |
| 2 | Balancing Gel Cleanser | cleanser | salicylic acid 0.5%, niacinamide | oiliness, pore, acne | AM/PM | not sensitive_ok |
| 3 | Everyday Foam Cleanser | cleanser | glycerin | (weak) oiliness | AM/PM | budget option |
| 4 | Niacinamide 5% Serum | serum | niacinamide, zinc PCA | oiliness, pore, age_spot, texture | AM/PM | versatile |
| 5 | Hyaluronic Hydration Serum | serum | sodium hyaluronate, panthenol | moisture | AM/PM | sensitive_ok |
| 6 | Vitamin C 10% Glow Serum | serum | ascorbyl glucoside, ferulic acid | age_spot, texture | **AM** | active `vitc` |
| 7 | Retinol 0.3% Night Serum | serum | retinol, squalane | wrinkle, texture | **PM** | active `retinoid`, not sensitive_ok, caution: SPF, patch test |
| 8 | Centella Calm Serum | serum | centella asiatica, allantoin | redness | AM/PM | sensitive_ok |
| 9 | Lactic Acid 5% Exfoliating Toner | toner_exfoliant | lactic acid | texture, age_spot, pore | **PM**, 2–3×/week | active `aha`, not sensitive_ok |
| 10 | Oil-Free Gel Moisturiser | moisturiser | glycerin, niacinamide | oiliness, acne | AM/PM | |
| 11 | Ceramide Barrier Cream | moisturiser | ceramides, cholesterol, shea | moisture, redness | AM/PM | sensitive_ok |
| 12 | Caffeine Eye Gel | eye | caffeine, hyaluronic acid | dark_circles | AM/PM | |
| 13 | Peptide Eye Cream | eye | peptides, niacinamide | dark_circles, wrinkle | PM | |
| 14 | Sheer Gel Sunscreen SPF 50 | sunscreen | chemical filters, no white cast | oiliness (finish), age_spot, wrinkle (prevention) | **AM** | required slot |
| 15 | Mineral Comfort Sunscreen SPF 50 (tinted) | sunscreen | zinc oxide, iron oxides (tint avoids white cast) | redness, age_spot | **AM** | sensitive_ok |

**Catalogue admission policy (the "no-bleach promise"):** no hydroquinone, mercury compounds, topical steroids, or "whitening / bleaching" positioning. A unit test asserts banned terms are absent.

**Copy rules:** "helps the look of", "formulated for"; never "treats", "cures", "heals", or names of conditions such as acne vulgaris, rosacea, melasma or eczema. A unit test greps the catalogue and UI strings for banned words.

### 9.2 Engine logic (plain language)
1. **Read the scores.** Use `raw_score` (honest), since higher means healthier **[V]**. Severity = `100 − raw_score`.
2. **Find priorities.** Rank the measured concerns by severity. Bands, our heuristic labelled as such:
   - **priority** = among the 3 most severe **and** `raw < 60`
   - **watch** = `raw < 75`
   - **good** otherwise
   - **not_measured** if missing

   If nothing is below 75: "Your skin looks balanced. Here's a maintenance routine."
3. **Weight concerns.** w_c = severity_c / Σ severity, across priority + watch concerns only. Skin type nudges cleanser and moisturiser texture.
4. **Filter products (hard rules):**
   - remove owned categories;
   - if fragrance-free, keep only `fragrance_free`;
   - if sensitive **or** redness is priority, drop non-`sensitive_ok` items (retinol, acids, BHA cleanser), noting what was dropped;
   - de-duplicate by `id`.
5. **Enumerate combinations** (15 products → at most 32,768 subsets, which takes milliseconds). A combination is valid if:
   - exactly one cleanser, moisturiser and sunscreen, unless owned;
   - ≤ 2 serums, ≤ 1 eye, ≤ 1 exfoliant;
   - total products ≤ routine-size limit;
   - cost ≤ budget.
6. **Score each combination:** coverage = Σ_c w_c × min(1, Σ_{p∈set} target_{p,c}). The `min(1, …)` caps each concern, so two products for the same concern don't double-count. That kills redundancy automatically. Add a small skin-type fit bonus. Subtract a tiny cost term (`0.0001 × cost / budget`) so the cheaper of two equal options wins, then fewer products.
7. **Pick the best.** Coverage % = coverage / Σ w_c.
8. **Build the routine:**
   - AM: cleanser → vitamin C / niacinamide / hydrating serum → eye → moisturiser → **sunscreen (last)**.
   - PM: cleanser → exfoliant **or** retinol (exfoliant 2–3×/week on non-retinol nights) → hydrating / calming serum → eye → moisturiser.
   - Vitamin C is AM only; retinol and exfoliant PM only.
   - If both retinol and exfoliant are selected: "Alternate nights; start retinol 2×/week."
9. **Explain.** For each product, each covered concern with weight > 0 produces a receipt, e.g. "Your texture scored 41/100 (higher is better) → lactic acid → helps smooth the look of uneven texture." Sunscreen always gets "Daily SPF protects the results of every other step."
10. **Alternatives.** For each slot, the top 3 other valid products by single-swap coverage.
11. **Total.** Sum the prices, state the budget status, list unaddressed concerns.

### 9.3 Pseudocode

```text
function recommend(metrics, skin_type, prefs, catalogue):
    measured = [m for m in metrics if m.raw_score is not None]
    if measured is empty: return error("no_metrics")
    for m in measured: m.severity = 100 - m.raw_score
    ranked = sort(measured, by severity desc)
    assign bands (top3 & raw<60 → priority; raw<75 → watch; else good)
    active = [m for m in ranked if m.band in {priority, watch}]
    if active empty: active = [] ; mode = "maintenance"
    weights = normalise({m.key: m.severity for m in active})

    pool = dedupe(catalogue)
    pool = [p for p in pool if p.category not in prefs.owned]
    if prefs.fragrance_free: pool = [p for p in pool if p.fragrance_free]
    if prefs.sensitive or band(redness) == priority:
        dropped = [p for p in pool if not p.sensitive_ok]; pool -= dropped

    required = {cleanser, moisturiser, sunscreen} - prefs.owned
    best = None
    for combo in subsets(pool, max_size = SIZE_LIMIT[prefs.routine_size]):
        if not valid_slots(combo, required): continue
        cost = sum(p.price for p in combo)
        if cost > prefs.budget: continue
        cov = sum(w * min(1, sum(p.targets.get(c,0) for p in combo)) for c, w in weights)
        cov += 0.02 * skin_type_fit(combo, skin_type)
        key = (cov - 0.0001*cost/prefs.budget, -len(combo))
        if best is None or key > best.key: best = (combo, key, cov, cost)

    if best is None:                              # budget too low
        core = cheapest_valid_core(pool, required)
        return result(core, status="over", over_by = cost(core) - prefs.budget,
                      warnings=["Budget below the cheapest complete basic routine"])
    routine = build_routine(best.combo)           # ordering, AM/PM, conflict + frequency rules
    receipts = explain(best.combo, weights, metrics)
    alts = alternatives(best.combo, pool, weights, prefs.budget)
    unaddressed = [c for c in weights if covered(best.combo, c) == 0]
    return result(best.combo, routine, receipts, alts, coverage_pct, total=best.cost, unaddressed)
```

### 9.4 Edge cases

| Case | Behaviour |
|---|---|
| Metric unavailable | `not_measured`, excluded from weights, shown in the UI |
| Metric uncertain (no confidence values exist **[V]**) | Copy "indicative, from one photo"; photo-quality tips; no absolute thresholds headlined |
| No relevant product for a concern | Listed in "unaddressed", honestly ("Our demo catalogue has nothing for X") |
| Budget insufficient | Cheapest valid core + "₦X over" + "Increase budget" button + "Mark items you own" hint |
| Products conflict | Rules in step 8; never retinol + AHA on the same night; vitamin C AM only |
| Catalogue duplicates | Startup validation fails on duplicate ids; engine de-dupes defensively |
| User owns everything core | Treatment-only routine; if no treatments are needed → "You're covered — keep going" |
| All concerns good | Maintenance routine (core three) |
| Sensitive + wrinkle priority | Retinol excluded with a note: "We skipped retinol because you marked sensitive skin" |

---
