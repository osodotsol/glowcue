# API Contracts

> **Status:** planned design from the GlowCue blueprint (research snapshot 31 Oct 2026). Nothing here is implemented unless [PROJECT_STATUS](PROJECT_STATUS.md) says so. Tags: **[V]** verified, **[A]** assumption, **[R]** recommendation, **[U]** unresolved.

### 7.4 API contracts

| Method & path | Request | Response | Notes |
|---|---|---|---|
| `GET /api/health` | — | `{"status":"ok"}` | Warm-up ping from the landing page |
| `GET /api/config` | — | `{"live_enabled":bool,"currency":"NGN","budget_default":30000,"budget_min":…,"budget_max":…,"disclaimer_version":"1"}` | |
| `POST /api/analyses` | `multipart/form-data`: `image` (jpg/png ≤ 10 MB), `consent=true` | `202 {"analysis_id":"uuid","status":"running"}` | 403 if live disabled or capped; 422 validation errors |
| `GET /api/analyses/{id}` | — | `{"status":"running"}` \| `{"status":"success","result":NormalizedAnalysis}` \| `{"status":"error","error":{"code":"face_too_small","message":"…","retryable":true}}` | Each call polls YouCam at most once; returns 404 after TTL |
| `GET /api/sample-analysis` | — | `{"status":"success","result":NormalizedAnalysis}` with `mode:"sample"` | Always available |
| `GET /api/catalogue` | — | `{"products":[Product]}` | |
| `POST /api/recommendations` | `{"metrics":[{"key","raw_score","ui_score"}],"skin_type":…,"preferences":Preferences}` | `RecommendationResult` | Stateless; scores only, no images |
| `POST /api/cart/quote` | `{"items":[{"product_id","qty"}]}` | `{"lines":[…],"subtotal":…,"currency":…}` | |
