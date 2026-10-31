# 04: Response normalisation and sample fixture

**Branch:** `feat/youcam-integration` · **Phase:** 2 · **Skill:** `/youcam-integration` · **Depends on:** 03 (real probe output)

## Objective
Convert YouCam JSON output into GlowCue's `NormalizedAnalysis`, and produce the sanitised recorded-sample fixture that powers "Try a recorded sample".

## Context
`docs/YOUCAM_API.md` §6.4–6.5 and §6.8, `docs/DATA_MODEL.md`, `docs/RECOMMENDATION_ENGINE.md` §9.2 step 2 (bands).

## Instructions
1. `services/normalize.py` is a pure function: `normalize(output: list[dict], masks: dict[str, bytes] | None, image_size) -> NormalizedAnalysis`.
   - Key map: `dark_circle_v2` → `dark_circles`. Other SD keys map one-to-one.
   - Use `raw_score` for severity and keep `ui_score`.
   - Compute bands: priority = top 3 **and** raw < 60, watch = raw < 75, good otherwise. Missing keys → `not_measured`.
   - Parse `skin_type` per the probe findings. Unknown types are logged and skipped.
2. Masks become data URLs (`data:image/png;base64,…`). Keep total payload ≤ 4 MB (downscale masks to the photo's displayed size if needed, preserving alpha).
3. Build `app/fixtures/sample_analysis.json` from the raw probe output:
   - strip `task_id`, `file_id`, URLs and request IDs;
   - set `mode: "sample"`;
   - masks stored as files in `app/fixtures/sample_masks/*.png`.
4. Sample photo: **ask the owner** whether to include the probe photo. If yes, commit with `GLOWCUE_PHOTO_APPROVED=1`. If no, generate a neutral face-silhouette SVG/PNG and use that as the base layer.
5. Switch `GET /api/sample-analysis` and mock mode to the real fixture, and delete `provisional_sample.json`.

## Expected files
`backend/app/services/normalize.py`, `backend/app/fixtures/{sample_analysis.json,sample_masks/*}`, `backend/tests/test_normalize.py`, `docs/YOUCAM_API.md` (fixture notes).

## Constraints
The normaliser is pure: no I/O and no settings. Never commit raw output. Never commit a photo without approval.

## Acceptance criteria
- The real fixture normalises to exactly 9 scored metrics plus skin type (or documented differences).
- The sample endpoint returns it with masks.
- The bands match the hand-calculated expectations in the test.

## Required tests
Real-fixture snapshot, the `dark_circle_v2` mapping, a missing metric, an unknown type, an all-good case (no priorities), band boundaries (59.9 / 60 / 74.9 / 75), and mask encoding.

## Definition of completion
Tests green, the secret scan is clean on the new fixtures, and the completion report includes the normalised summary table.
