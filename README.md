# GlowCue

**GlowCue turns one skin scan into the best routine your budget can buy, explains the reason for every product, and tells you honestly what that budget cannot cover.**

Built for the [YouCam API Skin AI & eCommerce VTO Hackathon](https://youcam-api-skin-ai-ecommerce.devpost.com/) with
Perfect Corp's **YouCam AI Skin Analysis API (v2.1, SD)**.

> **Cosmetic guidance only, not medical advice.** GlowCue never diagnoses or treats any skin condition.
> **Demo store:** every product is a fictional "GlowCue Demo" item, ingredient lists and prices (in ₦) are
> illustrative, and checkout is a preview: **no payment is taken and nothing is shipped.**

## The problem
A shopper with a fixed amount to spend (say ₦30,000 a month) has to decide which few skincare products are worth
buying for *their* skin. A skin-analysis app typically stops at scores, and a shop stops at a product list. Neither
answers the actual question: *with this budget, what should I buy, why, and what am I giving up?*

## What GlowCue does
1. **Consultation (4 short steps):** skin feel and type; up to three focus areas; preferences (fragrance-free, sensitive
   skin, ritual size); product types already on your shelf; your budget. Answers are used to build your recommendations, are kept in this browser session and are not saved to an account.
2. **Skin analysis:** a selfie analysed live by YouCam, or a clearly labelled demo profile (see [Modes](#demo-and-live-modes)).
3. **Skin report:** nine cosmetic attributes scored 1–100 (higher means healthier-looking), grouped into
   *priority*, *worth watching* and *looking good*, with a headline derived only from those groups.
4. **Budget-optimised ritual:** the morning and evening routine with the best coverage of your report that fits your
   budget, a one-sentence budget decision (budget, cost, money left, coverage), a reason for every product, the
   concerns the budget leaves uncovered, and instant re-planning when you change the budget or swap a product.
5. **Shop:** add the ritual to the bag, browse the edit, review the bag (totals re-quoted by the server), and see a
   checkout preview.

## How YouCam AI Skin Analysis is integrated
All YouCam traffic goes through one server-side module, `backend/app/services/youcam_client.py`. The API key never
reaches the browser.

1. `POST /s2s/v2.0/file`: register the upload and receive a presigned URL.
2. `PUT` the photo bytes to that URL, with exactly the returned headers and no API key.
3. `POST /s2s/v2.1/task/skin-analysis` with nine SD actions: `pore`, `dark_circle_v2`, `age_spot`, `moisture`,
   `oiliness`, `texture`, `redness`, `wrinkle`, `acne`. It also sends `format: "json"` and no mask overlay.
4. Poll `GET …/task/skin-analysis/{task_id}` about every 10 s until `success` or `error`.
   Only these status reads are retried; creating a task is never retried, because a retry could start a second
   analysis that is also charged.
5. `POST /s2s/v2.0/task/delete`: remove the task and its files from YouCam once finished.

GlowCue uses each concern's **`raw_score`**, the score predicted by the model. It never uses `ui_score`, which YouCam
documents as adjusted to look more favourable. A concern that is not returned is shown as *not measured*; nothing is
invented. The flow was verified live on 1 Nov 2026: all nine concerns came back inline as JSON, at 14 units per
analysis. Details and the verified response structure are in [docs/YOUCAM_API.md](docs/YOUCAM_API.md).

## From scores to recommendations
The engine (`backend/app/engine/`) is deterministic and has no AI-generated text.

- **Bands.** A concern is a *priority* if it is among the three lowest scores and below 60, *worth watching* if below
  75, otherwise *looking good*. These thresholds are GlowCue's own, not YouCam's.
- **Weights.** Each priority or watch concern is weighted by how visible it is (100 minus its score). Focus areas you
  chose in the consultation count 1.5 times as much, so a concern you care about still gets attention when its score
  is good.
- **Filters.** Fragrance-free and sensitive-skin preferences (or redness as a priority) remove unsuitable products.
  Product types already on your shelf are not recommended again.
- **Budget optimiser.** GlowCue tries *every* routine the catalogue allows, slot by slot (cleanser, moisturiser,
  sunscreen, up to two serums, eye care, exfoliant), within your ritual size (4, 6 or 8 products). It discards anything
  over budget and keeps the routine with the highest weighted coverage, plus a small bonus for suiting your skin type.
  Ties go to the cheaper routine, then the smaller one. If nothing fits, it shows the most affordable basic routine
  and says exactly how far over budget it is.
- **Coverage.** Each product has a strength (0 to 1) for each concern it targets. A concern's coverage is the sum
  across the routine, capped at 1, so doubling up earns nothing. The coverage figure is the weighted average across
  the concerns your report flagged.
- **Receipts.** Every product shows why it is there, using your real score. The format is:
  *"Your texture scored 49/100 (higher is better) → [the product's key ingredients] → helps smooth the look of uneven
  texture."*
- **Trade-offs.** Each product offers up to three same-type swaps, with the price difference, the coverage after the
  swap and whether it still fits the budget. Concerns the routine cannot reach are listed as *not covered at this
  budget*.
- **Routine order.** Sunscreen is always last in the morning. Vitamin C is morning only. Retinoids and acid exfoliants
  are evening only, never on the same night. Exfoliants are 2–3 evenings a week.
- **Your shelf.** Owned cleanser, moisturiser and sunscreen appear as *From your shelf* steps in their usual place.
  GlowCue has not seen these products, so their ingredients and suitability are not checked, and they are never added
  to the bag. An owned serum is not placed in the routine; use it as its label directs.

## Shopping demonstration
The bag shows server-quoted totals against your budget, plus a check that the essentials (cleanse, moisturise,
protect) are covered. The cart and checkout preview recompute every price on the server from the catalogue; the
client's prices are never trusted. The checkout preview can be printed as a ritual card. No payment is taken.

## Demo and live modes
| | Demo stories | Live analysis |
|---|---|---|
| Input | Choose one of four labelled skin profiles. **No photo leaves the browser.** | A selfie, sent only after the customer ticks an explicit consent box |
| Scores | Hand-written demonstration data, labelled *"Sample report"* with a note that it is not an analysis of the customer's photo | YouCam AI Skin Analysis, labelled *"Your skin report"* |
| Availability | Always | Only when the server enables it (below); otherwise the page shows the demo |

Live analysis needs **all three** of these on the server: `YOUCAM_MODE=live`, `LIVE_ANALYSIS_ENABLED=true` and an API
key. It is **off by default.** A failed live analysis never falls back to demo data silently. Photo problems (for
example the face too small or out of frame) come back with retake tips and the demo as an alternative.

## Privacy and safety
- **Consent first.** The server refuses a photo without consent, before reading it.
- **Photos stay in memory.** The browser re-encodes the photo (removing EXIF/GPS) before upload. The server checks the
  real file signature and size, then re-encodes it again into a fresh, metadata-free JPEG. Photos are never written to
  disk or logs, and GlowCue does not store them. After the analysis GlowCue asks YouCam to delete the task and its files; the
  request is accepted, but GlowCue cannot independently verify that the files are gone.
- **Camera stays local.** The in-app camera starts only when the customer taps *Take a selfie*. It records nothing
  and turns off as soon as a photo is taken or the camera is closed. The photo then goes through the same checks as a
  chosen file and is sent only with consent.
- **Scores expire.** Results live in an in-memory store for 30 minutes. The browser keeps only preferences, scores and
  the bag in `sessionStorage`, never the photo.
- **Spend and abuse limits.** There are per-visitor and global daily caps, and a unit-balance floor checked (free)
  before every upload.
- **Mock mode cannot reach YouCam.** Outside live mode the client is built so that any request fails before reaching
  the network.
- **Logs stay clean.** Logs never contain the key, Authorization headers, presigned or result URLs, task ids or image
  bytes.
- **Temporary imagery stays private.** `frontend/public/private/` holds temporary imagery for local development only.
  It is git-ignored, never referenced by production builds, and removed from `dist/` on every build, where
  `scripts/check-build-assets.mjs` fails the build if anything private remains.

More detail: [docs/SECURITY_PRIVACY.md](docs/SECURITY_PRIVACY.md).

## Run it locally
Requirements: Python 3.14 and Node.js 24.
```bash
git config core.hooksPath .githooks                       # secret-scan pre-commit hook

# Backend (mock mode by default, no API key needed): http://localhost:8000/api/health
cd backend
python -m venv .venv
.venv/Scripts/python -m pip install -r requirements-dev.txt      # macOS/Linux: .venv/bin/python
.venv/Scripts/python -m uvicorn app.main:app --reload

# Frontend: http://localhost:5173
cd ../frontend
npm install
npm run dev
```

### Configure the backend without exposing secrets
Copy `backend/.env.example` to `backend/.env` (git-ignored) and type the key there yourself. Never paste it into code,
chat, issues or commits. Settings are read only by `backend/app/config.py`. **Values in `backend/.env` take priority
over process environment variables**, so a command cannot switch a local server into live mode.

| Variable | Default | Purpose |
|---|---|---|
| `YOUCAM_API_KEY` | none | YouCam API key (server-side only) |
| `YOUCAM_MODE` | `mock` | `live` allows live analysis |
| `LIVE_ANALYSIS_ENABLED` | `false` | Kill switch; must also be `true` for live analysis |
| `PER_IP_PER_DAY` / `MAX_LIVE_PER_DAY` | `5` / `25` | Daily live-analysis caps |
| `CREDIT_FLOOR` | `100` | Refuse new analyses below this unit balance (`0` disables the check) |
| `YOUCAM_POLL_INTERVAL_S` / `YOUCAM_TASK_TIMEOUT_S` | `10` / `180` | Polling cadence and overall limit |
| `FRONTEND_ORIGIN` | `http://localhost:5173` | The deployed frontend's URL, allowed by CORS |
| `APP_ENV` | `development` | `production` allows **only** `FRONTEND_ORIGIN` (and refuses a localhost value); `development` also allows the local dev origins |

The frontend needs only `VITE_API_BASE_URL` (the public API address). In production there is no `.env` file: set the
variables as secrets on the host. Run **one** worker (the result store and caps are in memory), and enable proxy
headers so that per-visitor caps see real visitor addresses.

## Quality checks
```bash
python scripts/validate_project.py                                   # config and docs integrity
python scripts/security/check_secrets.py --all                       # secret scan
backend/.venv/Scripts/python -m pytest backend/tests scripts/tests -q
backend/.venv/Scripts/python -m ruff check backend scripts
cd frontend && npm run lint && npm run typecheck && npm test && npm run build   # build includes the asset-leak check
```
Backend tests can never reach the network or read the real key: they use a fake YouCam (`httpx.MockTransport`).

## Limitations
- The catalogue (15 products), ingredients and prices are fictional demonstration data.
- Shelf awareness is per product type, not per product. GlowCue does not check ingredient compatibility with products
  you own.
- The report shows scores, not YouCam's detection masks (the "skin map" is not enabled).
- Band thresholds (60 and 75) are GlowCue's choice and have been checked against only one real analysis so far.
- Results depend on the photo: YouCam needs a front-facing, evenly lit face filling most of the frame.
- Caps and results are held in memory, so they reset when the server restarts.

## Repository layout
| Path | What |
|---|---|
| `backend/` | FastAPI API: YouCam client, image checks, engine, catalogue, routes and tests |
| `frontend/` | React, TypeScript, Vite and Tailwind CSS v4 app |
| `docs/` | Product, architecture, API notes, decisions and status ([index](docs/README.md)) |
| `scripts/` | Project validator, secret scanner, guard tests |
| `.claude/`, `AGENTS.md`, `CLAUDE.md` | AI-assisted engineering rules, review agents and safety hooks |

## License
[MIT](LICENSE)
