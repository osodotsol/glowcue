# 18: Deployment (Render + Vercel)

**Branch:** `chore/release` · **Phase:** 6 · **Skill:** `/deployment-release` (manual) · **Depends on:** a merged `main` with a working sample journey

## Objective
Publish GlowCue: the API on Render's free tier and the SPA on Vercel Hobby, with correct env vars and CORS, verified on a phone.

## Context
`docs/DEPLOYMENT.md`, `.claude/skills/deployment-release/SKILL.md`, `docs/RUNBOOK.md`.

## Instructions
1. Add deploy config that contains **no secrets**:
   - `frontend/vercel.json` with an SPA rewrite to `/index.html`;
   - optionally `render.yaml` (blueprint) with the env var **names** only, `sync: false` for the key;
   - a `.python-version` consistent with Render support. If Render can't use 3.14, pin 3.12 everywhere and re-run tests.
2. Guide the owner click by click through Render (root `backend`, build and start commands, health path, env vars entered by the owner) and Vercel (root `frontend`, `VITE_API_BASE_URL`).
3. Set `FRONTEND_ORIGIN` to the Vercel URL and redeploy.
4. Verify:
   - `/api/health`;
   - the sample journey on the owner's phone (mobile data);
   - one owner-approved production live run (record units);
   - no key in the bundle (`grep` on `dist`);
   - CORS rejects other origins.
5. Add a release row to `docs/RUNBOOK.md`. Record the URLs in PROJECT_STATUS.

## Expected files
`frontend/vercel.json`, optional `render.yaml`, `.python-version`, `docs/RUNBOOK.md`, `docs/DEPLOYMENT.md` (actual values).

## Constraints
The owner enters secrets. Deploy only from `main`. Never commit URLs that contain tokens.

## Acceptance criteria
Both URLs are live, verified and recorded. The cold-start behaviour is acceptable (landing warm-up note shown).

## Required tests
The live verification checklist above, recorded with evidence.

## Definition of completion
Release recorded. Owner confirms the phone test.
