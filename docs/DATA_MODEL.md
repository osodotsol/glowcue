# Data Model

> **Status:** planned design from the GlowCue blueprint (research snapshot 31 Oct 2026). Nothing here is implemented unless [PROJECT_STATUS](PROJECT_STATUS.md) says so. Tags: **[V]** verified, **[A]** assumption, **[R]** recommendation, **[U]** unresolved.

### 7.5 Data models (Pydantic / TS mirror)

```text
Metric        { key: "oiliness"|"moisture"|"texture"|"pore"|"acne"|"redness"|"age_spot"|"wrinkle"|"dark_circles",
                label: str, raw_score: float|None, ui_score: int|None,
                band: "priority"|"watch"|"good"|"not_measured", rank: int|None,
                mask: str|None   # data URL or /static path
              }
NormalizedAnalysis { analysis_id, mode: "live"|"sample", image: {width, height},
                     metrics: [Metric], skin_type: {whole, t_zone, u_zone}|None,
                     overall_score: float|None, source: "YouCam AI Skin Analysis v2.1 (SD)" }
Preferences   { budget: int, currency, owned: ["cleanser"|"moisturiser"|"sunscreen"|...],
                fragrance_free: bool, sensitive: bool, routine_size: "minimal"|"balanced"|"complete" }
Product       { see [§9.1](RECOMMENDATION_ENGINE.md) }
RecommendationResult { priorities: [ {key,label,band,why_text} ],
                       selected: [ {product, slot, receipts:[Receipt], alternatives:[product_id]} ],
                       routine: { am:[Step], pm:[Step] }, coverage_pct, total, budget, budget_status:"within"|"over",
                       warnings:[str], skipped_owned:[category], unaddressed:[concern] }
Receipt       { concern_key, metric_raw_score, ingredient, claim_text }   # e.g. "Texture 41/100 → lactic acid → evens the look of rough texture"
Step          { order, product_id, instruction, frequency: "daily"|"2-3x weekly", note }
```

**Implemented shapes (1 Nov 2026).** The block above is the planning snapshot; the code is authoritative
(`backend/app/models.py`, mirrored in `frontend/src/lib/types.ts`):

```text
Metric             { key: <9 concern keys>, label, raw_score: float 1-100|null, ui_score: int|null, band }
NormalizedAnalysis { analysis_id, mode: "demo"|"live", provider, is_demo, profile_id|null, metrics: [Metric],
                     skin_type|null, notice }   # live: is_demo=false, skin_type=null (not requested), raw_score only
AnalysisJob        { analysis_id, status: "running"|"success"|"error", analysis: NormalizedAnalysis|null,
                     error: ErrorDetail|null }
ErrorDetail        { code, message, retryable, retake }   # retake=true: another photo is likely to fix it
```
