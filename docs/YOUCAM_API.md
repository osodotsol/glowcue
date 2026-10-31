# YouCam API Integration Notes

> **Status:** planned design from the GlowCue blueprint (research snapshot 31 Oct 2026). Nothing here is implemented unless [PROJECT_STATUS](PROJECT_STATUS.md) says so. Tags: **[V]** verified, **[A]** assumption, **[R]** recommendation, **[U]** unresolved.

## 6. YouCam API research

### 6.1 API selection [V]
**AI Skin Analysis v2.1** ([reference](https://docs.perfectcorp.com/reference/ai_skin_analysis.md), [OpenAPI YAML](https://docs.perfectcorp.com/_bundle/reference/ai_skin_analysis.yaml)). v2.1 (June 2026) has updated engines and up to 2560 px output ([changelog](https://docs.perfectcorp.com/release/changelog.md)). It costs the same as v2.0.

| Aspect | Verified detail |
|---|---|
| Base URL | `https://yce-api-01.makeupar.com` |
| Auth | Header `Authorization: Bearer <API_KEY>`. The key is generated in the console under API Keys. The FAQ says the secret key is shown **only once**, so save it immediately. |
| Step 1: register file | `POST /s2s/v2.0/file`, JSON `{"files":[{"content_type":"image/jpeg","file_name":"x.jpg","file_size":<bytes>}]}` → returns `data.files[0].file_id` and `requests[0].{method:"PUT", url, headers}` |
| Step 2: upload bytes | `PUT <presigned url>` with **exactly** the returned headers (`Content-Type`, `Content-Length`) and raw bytes. Skipping this gives 404 / 500 `unknown_internal_error` later. |
| Step 3: create task | `POST /s2s/v2.1/task/skin-analysis`, JSON `{"src_file_id": "...", "dst_actions": [...], "miniserver_args": {"enable_mask_overlay": false}, "format": "json"}` → `data.task_id`. Alternatively `src_file_url` with a public URL, which we won't use for privacy reasons. |
| Step 4: poll | `GET /s2s/v2.1/task/skin-analysis/{task_id}` → `data.task_status` ∈ `running` / `success` / `error`. Docs suggest polling e.g. every 10 s; results are kept 24 h. **Units are only consumed on `success`.** |
| Async | Yes. Webhooks exist but need a public endpoint and signature verification, so **use polling [R]**. |
| Format | `format: "json"` returns `data.results.output[]` items `{type, region?, raw_score, ui_score, score?, mask_urls[]}`. `"zip"` returns a URL (valid 2 h) to a ZIP containing `score_info.json` and PNG masks. **Use json [R].** |
| Image specs | jpg / jpeg / png, **< 10 MB**. **SD:** short side ≥ 480 px. **HD:** short side ≥ 1080 px. Long side > 2560 is auto-resized. The face must be > 60% of image width, front-facing, evenly lit; portrait orientation recommended. |
| Quality error codes | `error_below_min_image_size`, `error_exceed_max_image_size`, `error_src_face_too_small`, `error_src_face_out_of_bound`, `error_lighting_dark`, plus general `error_no_face`, `error_pose`, `error_face_parsing`, `error_nsfw_content_detected`, `unknown_internal_error` |
| Request errors | 400 `InvalidParameters` (including "cannot mix HD and SD dst_actions" and "Not available dst_action …"), `CreditInsufficiency`; 401 invalid key; 429 rate limit; 500 task timeout |
| Rate limit | 250 requests per 300 s per IP **and** per token ([rate limit](https://docs.perfectcorp.com/develop/rate_limit.md)) |
| Retention | Files and `file_id` 30 days; download URLs valid 2 h; everything auto-deleted after 30 days |
| Credits | `GET /s2s/v1.0/client/credit` (balance); `GET /s2s/v2.0/credit/feature-cost` ([unit system](https://docs.perfectcorp.com/reference/unit_system.md)) |
| Delete | `POST /s2s/v2.0/task/delete {"task_id": ...}` deletes the task **including input files and outputs** ([task management](https://docs.perfectcorp.com/reference/task_management.md)) |

### 6.2 SD vs HD decision [R]
**Use SD.** HD needs a short side ≥ 1080 px, but typical laptop webcams are 720p, and judges may test from laptops. SD needs only ≥ 480 px and is cheaper. HD's extra regional sub-scores are nice but not essential.

### 6.3 Selected concerns and cost
`dst_actions` = `["oiliness","moisture","texture","pore","acne","redness","age_spot","wrinkle","dark_circle_v2","skin_type"]`. That's 10 concerns, the **9–12 tier = 14 units per analysis (SD)** **[V]** ([unit table](https://docs.perfectcorp.com/reference/ai_skin_analysis.md)). 1,000 units ≈ **71 analyses**.

### 6.4 Attribute dictionary [V unless marked]

The docs state for every category: `raw_score` is a float 1–100 and `ui_score` an integer 1–100, and **"A higher score indicates healthier and more aesthetically pleasing skin condition."** Low score means more visible concern. The `ui_score` is "adjusted … to produce more favorable results". **No confidence values are returned.**

| Your target | Official key (SD) | Official description | Type / range | GlowCue interpretation |
|---|---|---|---|---|
| Oiliness | `oiliness` | "Determines skin oiliness" | float / int, 1–100 | Low = more visible shine/oil |
| Wrinkles | `wrinkle` | "General wrinkle analysis" | 1–100 | Low = more visible lines |
| Dark circles | `dark_circle_v2` (**not** `dark_circle` in SD) | "Analyzes dark circles" | 1–100 | Low = more visible under-eye darkness |
| Skin texture | `texture` | "Analyzes overall skin texture" | 1–100 | Low = more uneven-looking texture |
| (added) | `moisture` | "Measures skin hydration" | 1–100 | Low = drier-looking |
| (added) | `pore` | "Measures pore visibility" | 1–100 | Low = more visible pores |
| (added) | `acne` | "Evaluates acne presence" | 1–100 | Low = more visible blemishes (say "blemishes", never diagnose) |
| (added) | `redness` | "Measures skin redness" | 1–100 | Low = more visible redness → gentle-routine signal |
| (added) | `age_spot` | "Detects age spots" (HD: "age spots and pigmentation") | 1–100 | Low = more visible dark spots / uneven tone |
| (added) | `skin_type` | Subcategories whole / t_zone / u_zone: Normal, Oily, Dry, Combination, Redness, Dry & Redness, Oily & Redness, Combination & Redness | **[U] exact JSON shape** | Used to pick cleanser and moisturiser texture |
| — | `all.score` | Overall 1–100, higher = better | float | Show softly as "overall"; don't headline it |
| — | `skin_age` | AI-derived skin age | int | **Hidden by default** |

**All four target metrics are supported [V]. Watch for the `dark_circle_v2` naming.**

**[U] resolve in Phase 2:**
- How `skin_type` is represented in json output (label field? region?).
- Whether `region` appears on SD items.
- Whether `mask_urls` are PNGs with alpha at input resolution.
- The exact processing time.

### 6.5 Visualisation [V]
- **Available:** per-concern detection masks. With `enable_mask_overlay: false` (the default) you get "raw mask as .png", and the docs say "use the alpha values in these PNG files to blend them with your original image". `true` gives a single pre-blended JPG.
- **Not available:** facial landmarks or arbitrary segmentation assets from this endpoint. Only masks and scores.
- **Alignment rule (docs):** outputs are capped at 2560 px long side. If the input long side is under 2560, masks use the original resolution. **Because we pre-resize to ≤ 2048 px, the masks should match our image 1:1.** Render the photo and each mask in the same container with identical `width:100%; height:auto`, stacked with `position:absolute; inset:0`.
- **Expiring URLs:** download links are valid about 2 h. **[R]** The backend downloads masks immediately on success and returns them as data URLs, then (optionally) calls task delete. This also lets us delete YouCam's copy. Fallback: pass the URLs straight to `<img>` tags, which doesn't need CORS.
- **Transparency and legend:** an opacity slider (0–100%, default 70%) and one concern at a time, with the legend "Highlighted areas show where YouCam detected visible [concern]. Darker or denser highlights mean more detection." **[A]** Confirm the colour semantics from the real masks in Phase 2.
- **Fallback if masks fail:** show a text "where it shows up" list (SD has no regions, so just a score bar). **Never synthesise heatmaps.**

### 6.6 Account setup guide (you do this, Phase 0)
1. Log in on Devpost → [Join hackathon](https://youcam-api-skin-ai-ecommerce.devpost.com/). The email with your **redeem code** should arrive in about 2 min (check spam). Registered already? Search your inbox for "YouCam" or "Start Kit".
2. Sign up at [yce.perfectcorp.com/ai-api](https://yce.perfectcorp.com/ai-api) and verify your email.
3. Console → **Account → Redeem Code** → paste the code. The **1,000 units** appear immediately.
4. Console → **API Keys** → generate a key. **Copy it once into a password manager.** It won't be shown again.
5. Check units at [api-console](https://yce.makeupar.com/api-console/en/api-keys/) (the usage panel) or later via `GET /s2s/v1.0/client/credit`.
6. If the code fails, post on the forum and email `contact_event@PerfectCorp.com` with your YouCam **User ID** (the organisers asked for exactly this).

### 6.7 API testing strategy (evaluating yours)
Your 10-step plan is sound. Amendments:
- **Use the console's [API Playground](https://yce.makeupar.com/api-console/en/api-playground/ai-skin-analysis/)** **[V exists]** for the very first call. It's visual and confirms key and credits with no code. Then repeat the call once from our own probe script so the fixture comes from *our* code path.
- **Before any paid call, run two free calls:** `GET /client/credit` (key works) and `GET /credit/feature-cost` (prices).
- **Budget the units:**

  | Use | Units |
  |---|---|
  | Probe | ~3 × 14 = 42 |
  | Dev integration | ~5 × 14 = 70 |
  | Demo recording | ~4 × 14 = 56 |
  | Reserve | 100 (the backend refuses live runs below this) |
  | Public / judges | the remaining ~730 ≈ 52 analyses, capped by daily limits |

- **Fixture capture:** save (1) the raw JSON response; (2) the masks as PNG files; (3) the normalised result. **Sanitise:** remove `task_id`, `file_id` and URLs (masks are re-pointed to local files); keep scores. Store as `backend/app/fixtures/sample_analysis.json` plus `sample_masks/*.png` and `sample_photo.jpg` (only with consent, see [§20-F3](USER_CHECKLIST.md)).

**Modes [R]**
- `YOUCAM_MODE=mock`: the backend never touches the network. `POST /api/analyses` returns the fixture after a simulated 3 s delay. Used for all development and tests.
- `YOUCAM_MODE=live`: the real flow. Requires `YOUCAM_API_KEY`. Guarded by the per-IP and daily caps and the credit floor.
- **Independently**, `GET /api/sample-analysis` always serves the recorded fixture (labelled) for the public "Try sample" button.
- Production runs `live`, with sample mode as the default CTA.

---

### 6.8 Account verification log (free calls only — no units consumed)

| Date (WAT) | Check | Result |
|---|---|---|
| 31 Oct 2026 17:10 | `GET /s2s/v2.0/credit/feature-cost` with Bearer API key | **200** — key authenticates **[V]**. The SKU list did **not** include a Skin Analysis entry, so unit cost is taken from the docs table (14 units for 9–12 SD concerns) and must be confirmed by balance delta on the first live run **[U]**. |
| 31 Oct 2026 17:11 | `GET /s2s/v1.0/client/credit` with Bearer API key | **200** — `ApiPaygToken` amount **1000**, expiry `1801267199000` ms = **2027-01-29 23:59:59 UTC** **[V]**. `/s2s/v2.0/client/credit` returns 404 — use **v1.0** for balance checks. |

**Credential status (31 Oct 2026):** the first API key was pasted into a chat transcript and is treated as **exposed**. Policy: the owner revokes it in the console, generates a fresh key, and types it into `backend/.env` personally. Agents never read, print or reuse any key. The console's second value ("secret key", beginning `MIGfMA0…`) is an RSA **public** key used only by the legacy v1 access-token flow; GlowCue uses v2 Bearer API-key auth and does not need it.
