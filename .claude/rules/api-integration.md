---
paths:
  - "backend/app/services/youcam*.py"
  - "backend/app/services/normalize*.py"
  - "backend/app/fixtures/**"
  - "backend/scripts/**"
  - "docs/YOUCAM_API.md"
---
# External API integration rules (YouCam)

- **Facts first:** use only the endpoints, fields and error codes tagged [V] in `docs/YOUCAM_API.md`. If something is [U], resolve it with the owner-approved probe and record the result before relying on it.
- **Flow (v2.1 SD):**
  1. `POST /s2s/v2.0/file`
  2. `PUT` to the presigned URL with **exactly** the returned headers
  3. `POST /s2s/v2.1/task/skin-analysis` with `format: "json"` and `enable_mask_overlay: false`
  4. `GET …/{task_id}` polled until `success` or `error`
  5. Download the masks, then optionally `POST /s2s/v2.0/task/delete`
- **Never mix HD and SD actions.** The SD dark-circle key is `dark_circle_v2`.
- **Timeouts and retries:** every call has a timeout. Retry only on 429 and 5xx, at most 2 retries, with exponential backoff and jitter. Never retry a task creation that may have succeeded; poll instead.
- **Rate limits:** 250 requests per 300 s per IP and per token. Poll at ≥ 2 s intervals with a 90 s overall timeout.
- **Mock mode is the default** (`YOUCAM_MODE=mock`). Live mode requires `YOUCAM_API_KEY`, passes the caps and the credit floor, and is exercised **only** after the owner approves each run. Agents prefix approved commands with `GLOWCUE_LIVE_APPROVED=1`.
- **Unit accounting:** before and after every approved live run, read the balance (`GET /s2s/v1.0/client/credit`, free) and record the delta in `docs/YOUCAM_API.md` §6.8.
- **Validate responses defensively:** parse with Pydantic, tolerate unknown `type` values (log and skip) and treat missing ones as `not_measured`.
- **Sanitise fixtures before committing:**
  - strip `task_id`, `file_id`, presigned and mask URLs, and any request IDs;
  - keep scores;
  - store mask PNGs locally;
  - write raw responses only to the gitignored `backend/app/fixtures/raw/`.
