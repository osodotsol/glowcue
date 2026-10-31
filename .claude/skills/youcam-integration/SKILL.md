---
name: youcam-integration
description: How to build, test and operate GlowCue's YouCam AI Skin Analysis integration safely. Covers the verified v2.1 SD request flow, polling, mask handling, response normalisation, error mapping, mock vs live mode, fixture sanitisation and unit (credit) conservation. Use for any work on backend/app/services/youcam*, normalize*, fixtures, the probe script, or any question about YouCam API behaviour.
paths: "backend/app/services/**, backend/scripts/**, backend/app/fixtures/**"
---

# YouCam Integration

**Source of truth:** `docs/YOUCAM_API.md`. Re-read the relevant section before coding. If a fact you need is [U], stop and plan an approved probe; never guess.

## Prerequisites
- Mock mode works without a key. Live work requires the owner to have put a **fresh, rotated** key in `backend/.env`. You never read that file.

## Verified flow (v2.1, SD)
| # | Call | Notes |
|---|---|---|
| 1 | `POST /s2s/v2.0/file` `{files:[{content_type,file_name,file_size}]}` | Returns `file_id` and `requests[0]` with `{method:"PUT", url, headers}` |
| 2 | `PUT <url>` with exactly `headers` and raw bytes | Skipping this causes a later 404/500 |
| 3 | `POST /s2s/v2.1/task/skin-analysis` with `{src_file_id, dst_actions, miniserver_args:{enable_mask_overlay:false}, format:"json"}` | `dst_actions` = oiliness, moisture, texture, pore, acne, redness, age_spot, wrinkle, dark_circle_v2, skin_type (10 actions, 14 units [V docs]) |
| 4 | `GET /s2s/v2.1/task/skin-analysis/{task_id}` | `running`, `success` or `error`. Units are charged only on success. |
| 5 | Download `mask_urls` (they expire), then optionally `POST /s2s/v2.0/task/delete {task_id}` | The delete call is [U]; verify in the probe |
| — | `GET /s2s/v1.0/client/credit` | Free balance check [V 31 Oct] |

Auth header: `Authorization: Bearer <key>`. Base URL `https://yce-api-01.makeupar.com`.

## Procedure: changing the client or normaliser
1. Write or adjust tests with `httpx.MockTransport`, covering success, each mapped error, 429 retry, timeout, and an unknown `type`.
2. Implement in `services/youcam_client.py` (I/O only) and `services/normalize.py` (pure). Keep the error mapping in `services/youcam_errors.py`.
3. Run `backend/.venv/Scripts/python -m pytest backend/tests -q -k "youcam or normalize"`.
4. Update `docs/YOUCAM_API.md` if behaviour knowledge changed.

## Procedure: an owner-approved live run (probe or integration)
1. Ask the owner in plain words: "This will spend about 14 units of your remaining N. Approve?" Wait for an explicit yes.
2. Read the balance first. It's free, but the command still needs the approval token because it contacts the API host.
3. Run `backend/.venv/Scripts/python backend/scripts/probe_youcam.py <photo>`. The command guard will put a **permission prompt in front of the owner**, and the run only proceeds if they approve it there. Nothing you add to the command can skip that prompt, and you must not try to.
4. Read the balance again and record date, purpose, delta and result in `docs/YOUCAM_API.md` §6.8.
5. **Sanitise** before anything is committed:
   - keep scores;
   - drop `task_id`, `file_id`, URLs and request IDs;
   - re-point masks to local files.

   Raw output goes only to the gitignored `backend/app/fixtures/raw/`.

## Quality checks
- No key in code, logs or fixtures (`python scripts/security/check_secrets.py --all`).
- Rankings use `raw_score`. Higher means healthier. `ui_score` is shown only with the honesty note.
- HD and SD actions are never mixed. A missing metric becomes `not_measured`.

## Output and completion
Tests green, docs updated, the unit ledger updated after any live run, no secrets.
