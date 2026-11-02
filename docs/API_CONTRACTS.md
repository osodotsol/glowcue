# API Contracts

> **Status:** planned design from the GlowCue blueprint (research snapshot 31 Oct 2026). Nothing here is implemented unless [PROJECT_STATUS](PROJECT_STATUS.md) says so. Tags: **[V]** verified, **[A]** assumption, **[R]** recommendation, **[U]** unresolved.

### 7.4 API contracts

| Method & path | Request | Response | Notes |
|---|---|---|---|
| `GET /api/health` | — | `{"status":"ok"}` | Warm-up ping from the landing page |
| `GET /api/config` | — | `live_enabled` is true only when `YOUCAM_MODE=live`, `LIVE_ANALYSIS_ENABLED=true` and a key is set. `{"mode":"demo","live_enabled":false,"currency":"NGN","budget_default":30000,"budget_min":5000,"budget_max":150000,"disclaimer":"…"}` | **Implemented** (first product slice, 31 Oct 2026) |
| `GET /api/demo-profiles` | — | `[{"id","name","summary"}]` | **Implemented.** Four labelled demo skin profiles |
| `POST /api/analyses/demo` | `{"profile_id":"uneven-tone"}` (JSON; extra fields such as an image are rejected) | `NormalizedAnalysis` with `mode:"demo"`, `is_demo:true`, a demo `notice`, and each metric's `band` from the engine | **Implemented.** Never receives a photo ([ADR-005](decisions/ADR-005-demo-provider-and-redesign.md)) |
| `POST /api/analyses?consent=true` | The photo itself as the raw body, `Content-Type: image/jpeg` or `image/png`, ≤ 10 MB (not multipart: Starlette spools multipart uploads over 1 MB to disk). Refused before the photo is read unless live analysis is on (`503 live_unavailable`) and `consent=true` (`422 consent_required`). Then: real JPEG/PNG signature (`415 invalid_image`), size (`413 image_too_large`), daily caps (`429 daily_limit_reached`), reserved **before** any decoding; then decoding in a worker thread: short side ≥ 480 px (`422 image_too_small`), too many photos being prepared at once (`503 busy`, retryable). A failure after the reservation releases it. | `202 AnalysisJob` `{"analysis_id":"live-…","status":"running","analysis":null,"error":null}` | **Implemented offline** (Phase A, 1 Nov 2026; fake-YouCam tests only, no live call yet) |
| `GET /api/analyses/{analysis_id}` | — | `AnalysisJob`: `status` `running` \| `success` (+ `analysis`: `NormalizedAnalysis` with `mode:"live"`, `is_demo:false`) \| `error` (+ `error`: `{code, message, retryable, retake}`). `404 unknown_analysis` after 30 min. | **Implemented offline** (Phase A) |
| `GET /api/catalogue` | — | `{"disclaimer","currency","products":[Product]}`; each product has a `pack` shape instead of an image path | **Implemented** |
| `POST /api/recommendations` | `{"metrics":[{"key","raw_score"}],"skin_type":…,"preferences":Preferences}` (`pinned` = swapped-in product ids) | `RecommendationResult` | **Implemented.** Stateless; scores only, no images |
| `POST /api/cart/quote` | `{"items":[{"product_id","qty"}]}` | `{"lines":[…],"subtotal","currency","item_count","notice"}` | **Implemented.** Prices from the catalogue only; client prices rejected |
