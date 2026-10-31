# 12: Heatmap viewer

**Branch:** `feat/frontend-experience` · **Phase:** 4 · **Skill:** `/frontend-engineering` · **Depends on:** 11, 04

## Objective
Show YouCam's own per-concern detection masks aligned over the photo, with controls and an accessible text equivalent.

## Context
`docs/YOUCAM_API.md` §6.5 (mask facts: PNG alpha, input-resolution alignment) and the §6.8 probe findings, `docs/DESIGN_SYSTEM.md` §8.3 (Results row).

## Instructions
1. `components/HeatmapViewer.tsx`:
   - one relative container; the photo (or neutral silhouette in sample mode) as `<img class="w-full h-auto">`;
   - the selected mask as an absolutely positioned `<img>` (`inset-0 w-full h-full`) with the same aspect ratio (use the `image.width/height` from the result);
   - concern chips for the measured metrics that have masks;
   - an opacity slider (0–100, default 70) with a label;
   - a legend: "Highlighted areas show where YouCam detected visible <concern>."
2. Text equivalent: a visually adjacent line, e.g. "Texture: 41/100 (higher is better). Priority."
3. Concerns without a mask show the note "No map for this concern".
4. Keyboard: the chips are a radio group (arrow keys), and the slider is accessible.
5. Integrate into Results, and highlight the matching metric row when a chip is selected.

## Expected files
`frontend/src/components/HeatmapViewer.tsx`, `frontend/src/pages/Results.tsx`.

## Constraints
**Never** generate or synthesise heatmaps. Only display masks returned by YouCam. No canvas pixel manipulation, which would need CORS.

## Acceptance criteria
With the sample fixture, masks align with the base image at 375 and 1280 px (visual check, plus Antigravity). The slider changes opacity. Everything is reachable by keyboard.

## Required tests
Lint, typecheck and build. A manual alignment check is recorded in the report. Antigravity report for the Results screen.

## Definition of completion
Report, then the `feat/frontend-experience` PR via prompt 19 after `/design-review`.
