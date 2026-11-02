---
name: hackathon-submission
description: Prepares and checks every GlowCue hackathon deliverable. Covers Devpost text, screenshots, the demo video script, the YouCam integration explanation, repository readiness, links, judging-criteria alignment, eligibility statements and the final compliance checklist. Manual-only. The owner performs the actual Devpost submission and video upload.
disable-model-invocation: true
argument-hint: "[draft|screenshots|video|check]"
---

# Hackathon Submission

Sources:
- `docs/SUBMISSION_CHECKLIST.md` (verified rules + final checklist)
- `docs/submission/DEVPOST_DRAFT.md`
- `docs/submission/DEMO_STORYBOARD.md`
- `docs/submission/SCREENSHOT_PLAN.md`

Deadline: **Mon 2 Nov 2026 11:45 EST = 17:45 WAT**. Internal target: **14:00 WAT**.

## Procedure
1. **draft:** refresh `docs/submission/DEVPOST_DRAFT.md` with **real** numbers from PROJECT_STATUS (tests passed, units used, timings, URLs). Map each section to the four equally weighted criteria: Technological Implementation, Design, Potential Impact, Quality of Idea.
2. **screenshots:** follow `SCREENSHOT_PLAN.md`. Capture in sample mode with Playwright at 1440×900 and 390×844, saving to `docs/screenshots/`. Check that no key, email or unapproved face is visible.
3. **video:** finalise the narration (≤ 330 words for 2:20) and shot list in `DEMO_STORYBOARD.md`. It must:
   - name **YouCam AI Skin Analysis API v2.1**;
   - show the app working on its device;
   - contain no third-party trademarks or copyrighted music;
   - be uploaded **Public** to YouTube.

   The owner records and uploads.
4. **check:** walk through every box in `SUBMISSION_CHECKLIST.md` §21 with evidence:
   - the repo is public, has the MIT licence, and its README setup works from a fresh clone;
   - `check_secrets --all` and `--history` are clean;
   - the app URL works in incognito;
   - the video is public and 1–3 min;
   - every link returns 200 (`curl -s -o /dev/null -w "%{http_code}" <url>`).
5. **Eligibility:** state only facts the owner has confirmed. Opt into Women in Tech or Rising Star **only** if the owner explicitly confirms eligibility. Rising Star needs a school-issued email. Never infer eligibility.
6. **Hand over** a final summary listing each Devpost field and its source file, so the owner can paste it in. The owner clicks Submit and confirms the status shows "Submitted".

## Completion criteria
Every checklist item is ticked with evidence. The owner has submitted before 14:00 WAT. `main` is frozen afterwards.
