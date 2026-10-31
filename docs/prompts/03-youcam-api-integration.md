# 03: YouCam API integration and live probe

**Branch:** `feat/youcam-integration` · **Phase:** 2 · **Skill:** `/youcam-integration` · **Depends on:** 02 · **Reviewer:** `api-researcher` before coding, `backend-reviewer` after

## Objective
Build the YouCam client exactly as documented, wire live mode behind all guards, and run **one owner-approved probe** that captures a real response and resolves the open questions.

## Context
`docs/YOUCAM_API.md` (all of it), `.claude/rules/api-integration.md`, `docs/decisions/ADR-002-api-integration.md`, `docs/implementation/PHASE_2_API.md`.

## Instructions
1. Ask the `api-researcher` subagent to re-confirm the v2.1 request schema and the delete endpoint from the official docs (no calls).
2. `services/youcam_client.py` (httpx.AsyncClient, base `https://yce-api-01.makeupar.com`, Bearer from settings):
   - `register_file(size, content_type)`
   - `upload(presigned)`
   - `create_task(file_id)` with the 10 SD `dst_actions`, `enable_mask_overlay=false`, `format="json"`
   - `get_task(task_id)`
   - `download_mask(url)`
   - `delete_task(task_id)`
   - `get_credit()`

   Timeouts: connect 10 s, read 30 s. Retry 429 and 5xx at most twice with backoff, never on create.
3. `services/youcam_errors.py`: map every documented error code to `(friendly_code, message, retryable)`. Examples: `error_src_face_too_small` → `face_too_small` ("Move closer so your face fills most of the frame"), `CreditInsufficiency` → `service_unavailable`.
4. Live path in `routes/analyses.py`, behind `YOUCAM_MODE=live`, `LIVE_ANALYSIS_ENABLED`, the caps and the credit floor (cached credit check, 5 min).
5. `backend/scripts/probe_youcam.py <photo>`:
   - prints the balance before and after;
   - runs the flow once;
   - saves the raw JSON and masks to `backend/app/fixtures/raw/` (gitignored) with timing;
   - tries `delete_task` and reports the result;
   - never prints the key.
6. **Stop and ask the owner:** "Approve one live probe (~14 units of N)?" Only after a clear yes, run `GLOWCUE_LIVE_APPROVED=1 backend/.venv/Scripts/python backend/scripts/probe_youcam.py <owner-provided photo path>`.
7. Record in `docs/YOUCAM_API.md` §6.8: units delta, duration, the `skin_type` output shape, `region` presence, mask format and dimensions vs input, delete result. Flip the resolved [U] tags to [V].

## Expected files
`backend/app/services/{youcam_client.py,youcam_errors.py}`, `backend/app/routes/analyses.py`, `backend/scripts/probe_youcam.py`, `backend/tests/test_youcam_client.py`, `docs/YOUCAM_API.md`.

## Constraints
At most 3 live runs in this prompt, each separately approved. No key in logs or output. The photo is supplied by the owner and never committed without approval.

## Acceptance criteria
Client tests green with no network. The probe succeeded and its findings are documented. Live mode refuses requests when the kill switch, caps or floor apply.

## Required tests
MockTransport tests: the happy path across all 4 calls, every mapped error, 429 then success, timeout, polling to error, unknown output type ignored, and redaction (the key never appears in the exception string).

## Definition of completion
The above, plus the unit ledger updated and the completion report including the units spent.
