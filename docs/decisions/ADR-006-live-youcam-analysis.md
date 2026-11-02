# ADR-006: Live YouCam skin analysis (Phase A, offline build)

- **Status:** Accepted, 1 Nov 2026. The owner accepted the feasibility audit and authorised Phase A. No live call has been made yet.

## Context
GlowCue's report and recommendation engine already run on nine concern keys scored 1–100, where higher means healthier-looking skin. The official docs confirm that YouCam AI Skin Analysis SD returns the same semantics in `raw_score`. Live analysis has to:
- send a customer's photo to a third party only with explicit consent;
- keep the API key and the photo safe;
- never present demo data as a real result;
- spend scarce units only when the owner allows it.

## Options considered
| Topic | Options | Choice |
|---|---|---|
| Request shape | Synchronous request that waits for YouCam · job id plus polling | **Job id plus polling** (`202`, then `GET /api/analyses/{id}`). Processing time is undocumented. |
| Upload format | `multipart/form-data` · raw request body | **Raw body.** Starlette spools multipart files over 1 MB to disk; photos must stay in memory. |
| Actions | 10 (with `skin_type`) · 9 · add `radiance` | **9 SD actions, no `skin_type`.** Its output label is undocumented; the self-reported skin type is used instead. Same 14-unit tier. |
| Scores | `raw_score` · `ui_score` | **`raw_score` only.** `ui_score` is documented as adjusted to be more favourable. |
| Missing concerns | Fill from demo or averages · mark `not_measured` | **`not_measured`.** Nothing is invented. |
| Demo in live mode | Replace with live · keep as an explicit choice | **Keep.** The demo is always available and labelled. A live failure never falls back to demo silently. |
| Version uncertainty | Assume v2.1 accepts v2.0 file ids · make it switchable | **Switchable** (`YOUCAM_TASK_API`). Confirmed 1 Nov 2026 (no-face probe): v2.1 accepts a v2.0 file id, so the switch stays at `v2.1`. |
| Retries | Retry everything · reads only | **Reads only** (GET, ≤ 2 retries). A retried task creation could bill twice. |

## Decision
The live path is split into small pieces:
- `services/youcam_client.py`: the only YouCam I/O.
- `services/normalize.py`: pure mapping.
- `services/youcam_errors.py`: one error table.
- `services/image.py`: in-memory validation and re-encoding.
- `services/limits.py`: daily caps.
- `services/analysis/live.py`: background run plus 30-minute store.
- `routes/analysis.py`: the two endpoints.

The safeguards are B1–B6 in [SECURITY_PRIVACY](../SECURITY_PRIVACY.md) §4.4.

## Consequences
- Live analysis stays off until the owner sets `YOUCAM_MODE=live` and `LIVE_ANALYSIS_ENABLED=true` in `backend/.env`.
- The first live run is the probe script, and it settles the [U] items in [YOUCAM_API](../YOUCAM_API.md) §6.9.
- Single worker only (in-memory store and caps).
- Behind a proxy, the per-IP cap sees the proxy's address unless Uvicorn runs with proxy headers. Revisit at deployment.
