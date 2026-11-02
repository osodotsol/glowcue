# 11: Analysis interface (processing and results)

**Branch:** `feat/frontend-experience` · **Phase:** 4 · **Skill:** `/frontend-engineering` · **Depends on:** 09, 10, 04

## Objective
An honest processing experience, and a Results page that makes the skin priorities understandable in plain language.

## Context
`docs/DESIGN_SYSTEM.md` §8.3 (Processing and Results rows), `docs/PRD.md` F3, F5, `docs/RECOMMENDATION_ENGINE.md` §9.2 step 2 (bands), `docs/YOUCAM_API.md` §6.4 (score meaning).

## Instructions
1. `pages/Processing.tsx`:
   - poll `GET /api/analyses/:id` every 2 s, with a 90 s timeout;
   - staged messages in an `aria-live` region;
   - cancel link;
   - on error, show the mapped friendly message with **Try another photo** and **Use recorded sample**;
   - on success, store the result in SessionContext and go to `/results`.
2. `pages/Results.tsx`:
   - **Top 3 priorities** cards: concern label, band chip, one-line plain explanation, raw score;
   - an all-metrics list using `ScoreBar` (raw score, "higher is better");
   - a skin-type summary;
   - a placeholder slot for the HeatmapViewer (prompt 12);
   - an **"About these scores"** accordion. It explains that YouCam provides a raw model score and a friendlier display score, that GlowCue ranks on the raw score for honesty, that no confidence values are provided, that scores are indicative from one photo, and that this is cosmetic, not medical;
   - a **Recorded sample** badge when `mode === "sample"`;
   - CTA **Build my routine** → `/routine`.
3. If there's no result in the session (e.g. after a refresh), show a friendly "Start again" empty state.
4. Concern labels and explanations go in `lib/concerns.ts` (one source).

## Expected files
`frontend/src/pages/{Processing.tsx,Results.tsx}`, `frontend/src/lib/concerns.ts`, `frontend/src/components/PriorityCard.tsx`.

## Constraints
No medical or alarmist language. Never headline `ui_score`, and never show skin age.

## Acceptance criteria
The sample flow shows correct priorities that match the backend bands. Error states are reachable with mocked responses. Layout works at 375 and 1280 px.

## Required tests
Vitest for `concerns.ts` mapping and any formatting helpers. Lint, typecheck and build.

## Definition of completion
Report, followed by an Antigravity checkpoint suggestion.
