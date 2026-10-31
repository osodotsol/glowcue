# 21: Demo production (screenshots and video script)

**Branch:** `docs/submission` · **Phase:** 7 · **Skill:** `/hackathon-submission` (manual) · **Depends on:** 18, 20

## Objective
Produce genuine screenshots and a ready-to-record 2:20 demo script. The owner records and uploads the video.

## Context
`docs/submission/SCREENSHOT_PLAN.md`, `docs/submission/DEMO_STORYBOARD.md`, `docs/SUBMISSION_CHECKLIST.md` §2 (video rules).

## Instructions
1. `frontend/e2e/screenshots.spec.ts` (Playwright, sample mode, against the deployed URL or local): capture the 6 shots in SCREENSHOT_PLAN to `docs/screenshots/`. Hide dev overlays and use a clean state.
2. Check each screenshot: no keys, emails or bookmarks, and no face except the approved sample or silhouette.
3. Finalise `DEMO_STORYBOARD.md`:
   - the narration (≤ 330 words, plain English) must say "YouCam AI Skin Analysis API, version 2.1";
   - a shot list with timestamps;
   - pre-recording setup: clean browser profile, 110% zoom, notifications off, cart cleared, sample and live paths ready;
   - recording tips: OBS or the Windows Snipping Tool recorder, 1080p, mic test, no music or YouTube Audio Library only;
   - an upload checklist: YouTube **Public**, title "GlowCue — YouCam AI Skin Analysis hackathon demo", description with links, corrected captions.
4. Hand the owner the script and checklist. **Don't record or upload.**

## Expected files
`docs/screenshots/*.png`, `frontend/e2e/screenshots.spec.ts`, `docs/submission/DEMO_STORYBOARD.md`.

## Constraints
Screenshots must come from the real app, not mock-ups. No third-party trademarks or music.

## Acceptance criteria
6 screenshots match the plan. The script reads in ≤ 2:30 aloud (owner test read).

## Required tests
Screenshot spec runs green.

## Definition of completion
Owner has the script. Screenshots committed.
