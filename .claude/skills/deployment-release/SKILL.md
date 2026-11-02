---
name: deployment-release
description: Deploys GlowCue (FastAPI backend on Render free tier, React frontend on Vercel Hobby), configures environment variables and CORS, verifies the live deployment, and documents rollback. Manual-only because it touches external services and secrets.
disable-model-invocation: true
argument-hint: "[backend|frontend|verify|rollback]"
---

# Deployment and Release

Guide: `docs/DEPLOYMENT.md`. Runbook: `docs/RUNBOOK.md`.

## Prerequisites
- `main` contains a merged, CI-green release candidate. Deploy from `main` only.
- The owner has Render and Vercel accounts linked to GitHub, plus a **fresh** YouCam key, which the owner pastes into Render personally.

## Procedure
1. **Pre-flight:** run `/test-and-verify all` and `/security-review`. Both must be green and free of High findings.
2. **Backend (Render), owner clicks and Claude guides:**
   - New, then Web Service, then select the repo. Root directory `backend`. Runtime Python.
   - Build command: `pip install -r requirements.txt`
   - Start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT --workers 1`
   - Health check path: `/api/health`
   - Env vars (owner enters them; never in a committed file):

     | Name | Value |
     |---|---|
     | `YOUCAM_API_KEY` | secret |
     | `YOUCAM_MODE` | `live` |
     | `LIVE_ANALYSIS_ENABLED` | `true` |
     | `MAX_LIVE_PER_DAY` | `25` |
     | `PER_IP_PER_DAY` | `5` |
     | `CREDIT_FLOOR` | `100` |
     | `FRONTEND_ORIGIN` | the Vercel URL |
     | `CURRENCY` | `NGN` |
     | `PYTHON_VERSION` | match `.python-version` |
3. **Frontend (Vercel):** import the repo with root directory `frontend`, framework Vite. Set env `VITE_API_BASE_URL=https://<service>.onrender.com`. `frontend/vercel.json` rewrites SPA routes.
4. **CORS:** set the Render `FRONTEND_ORIGIN` to the exact Vercel production URL, then redeploy.
5. **Verify** and record the results in `docs/PROJECT_STATUS.md`:
   - `curl -s https://<api>/api/health` returns `{"status":"ok"}`;
   - the full sample journey works on the owner's phone over mobile data;
   - one **owner-approved** live analysis works (record the unit delta in `docs/YOUCAM_API.md` §6.8);
   - the browser console is clean;
   - no key appears in the frontend bundle.
6. **Release notes:** add a dated entry to `docs/RUNBOOK.md` (Releases) with the commit SHA, URLs and verification results.

## Rollback
- **Render:** Events, then the previous deploy, then "Rollback to this deploy".
- **Vercel:** Deployments, then the previous one, then "Promote to Production".
- **Emergency quota stop:** set `LIVE_ANALYSIS_ENABLED=false` on Render. Sample mode keeps working.

## Completion criteria
Both URLs are live and verified, and the release is recorded. After submission, `main` is frozen until judging ends (21 Nov 2026).
