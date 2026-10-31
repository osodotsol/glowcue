# Deployment Guide

> **Status:** planned design from the GlowCue blueprint (research snapshot 31 Oct 2026). Nothing here is implemented unless [PROJECT_STATUS](PROJECT_STATUS.md) says so. Tags: **[V]** verified, **[A]** assumption, **[R]** recommendation, **[U]** unresolved.

## 14. Deployment strategy

| Option | Free tier | Python | Notes | Verdict |
|---|---|---|---|---|
| **Render (web service)** | Free; **spins down after ~15 min idle, ~30–60 s cold start**; 750 instance-h / month ([third-party summary](https://livemy.app/blog/render-pricing)) **[V-ish]** | Native | Simple GitHub deploy, env vars, `$PORT` | **Backend [R]** |
| **Vercel Hobby** | Free static hosting, global CDN | n/a | Instant load hides backend cold start; SPA rewrite needed | **Frontend [R]** |
| Netlify / Cloudflare Pages | Free static | n/a | Equal alternatives to Vercel | Fallback |
| Hugging Face Spaces | Free CPU sleeps after ~48 h idle; **Docker Spaces may now require PRO** **[U]** | Docker | Uncertain | Not chosen |
| Railway / Fly.io | Trial credit, or a card required | — | Cost risk | Avoid |
| Single Render service serving the React build | Free | — | One deploy, but a cold start blanks the whole page | Fallback if CORS issues arise |

**Cold-start mitigation:** the landing page pings `/api/health` on load, and the sample button shows "Warming up the analysis server…" if needed. Optionally add a free [cron-job.org](https://cron-job.org) ping every 14 min **during the judging window only**. Community reports say this isn't officially supported, so treat it as best-effort.

**Steps:**
1. Push to GitHub.
2. Render → New Web Service → repo → root `backend` → build/start commands from P17 → env vars:
   - `YOUCAM_MODE=live`, `YOUCAM_API_KEY`, `LIVE_ANALYSIS_ENABLED=true`
   - `MAX_LIVE_PER_DAY=25`, `PER_IP_PER_DAY=5`, `CREDIT_FLOOR=100`
   - `FRONTEND_ORIGIN`, `CURRENCY`, `PYTHON_VERSION`
3. Health check `/api/health`.
4. Vercel → import repo → root `frontend` → `VITE_API_BASE_URL=https://<render>.onrender.com`.
5. Set Render `FRONTEND_ORIGIN` to the Vercel URL → redeploy.
6. Verify: sample flow on phone; one live run; check the balance.

**Cost:** ₦0 / $0. A custom domain is optional (~$10–15 per year) and not needed.

**Through 21 Nov:** don't push breaking changes after submission (keep `main` frozen; work on branches). Watch credits weekly; lower `MAX_LIVE_PER_DAY` if needed. The sample mode guarantees judges can always test.

---
