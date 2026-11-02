# 22: Devpost submission

**Branch:** `docs/submission` · **Phase:** 7 · **Skill:** `/hackathon-submission check` (manual) · **Depends on:** 21 and the video uploaded by the owner

## Objective
A complete, compliant, compelling Devpost entry submitted by **Mon 2 Nov, 14:00 WAT**.

## Context
`docs/submission/DEVPOST_DRAFT.md`, `docs/SUBMISSION_CHECKLIST.md` (§2 rules, §21 checklist), `docs/PROJECT_STATUS.md` (real numbers).

## Instructions
1. Finalise `DEVPOST_DRAFT.md` with real figures (tests passed, units used, analysis time, URLs). Map each section to Technological Implementation, Design, Potential Impact and Quality of Idea.
2. Testing instructions for judges: the sample path (no upload needed), live path limits, and the cold-start note.
3. Eligibility: include only what the owner confirms (submitter type, special-award opt-ins, school email for Rising Star). Never infer it.
4. Check every link (repo public, app URL, YouTube public): each returns 200 in incognito.
5. Run the full §21 checklist with evidence, including `check_secrets.py --all` and `--history`.
6. Give the owner a field-by-field paste sheet. **The owner submits** and confirms the status shows "Submitted".
7. After submission: freeze `main`, record the submission time in PROJECT_STATUS, and set a reminder to monitor the app and units until 21 Nov.

## Expected files
`docs/submission/DEVPOST_DRAFT.md`, `docs/PROJECT_STATUS.md`.

## Constraints
No exaggerated claims. No unverified eligibility. Don't submit on the owner's behalf.

## Acceptance criteria
All §21 items ticked with evidence. Submitted before 14:00 WAT.

## Required tests
Link checks, secret scans, a final sample-journey check on the deployed app.

## Definition of completion
Devpost shows "Submitted". PROJECT_STATUS records it.
