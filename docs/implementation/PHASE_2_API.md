# Phase 2: YouCam API client, live probe and normalisation

**Objective:** a verified, tested YouCam client; **one owner-approved live probe** that captures a real response; and a normaliser that turns it into GlowCue's `NormalizedAnalysis`.
**Prompts:** [03-youcam-api-integration](../prompts/03-youcam-api-integration.md), [04-response-normalization](../prompts/04-response-normalization.md) · **Branch:** `feat/youcam-integration` · **Depends on:** Phase 1 · **Skill:** `/youcam-integration` · **Reviewer:** `api-researcher` (docs), `backend-reviewer`

## Gate: before any live call
- [ ] The owner has rotated the key and placed it in `backend/.env`.
- [ ] The owner explicitly approves the run in chat ("approve live probe, ~14 units").
- [ ] The balance is read before and after (free) and recorded in [YOUCAM_API §6.8](../YOUCAM_API.md).

## Acceptance checks
- [ ] Client unit tests (MockTransport): success, every mapped error, 429 retry, timeout, unknown type.
- [ ] Probe completed. Every [U] in YOUCAM_API §6.4–6.5 resolved or given a documented workaround (`skin_type` shape, mask format and size, delete endpoint, real unit cost).
- [ ] Sanitised fixture committed (`sample_analysis.json`, masks). Raw output only in the gitignored `fixtures/raw/`.
- [ ] Sample photo committed **only** with explicit owner approval. Otherwise sample mode uses masks over a neutral silhouette.
- [ ] `GET /api/sample-analysis` serves the normalised fixture.

## Units budget
Probe ≤ 3 runs (≤ 42 units).
