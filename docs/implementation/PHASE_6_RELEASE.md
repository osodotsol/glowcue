# Phase 6: Deployment and documentation

**Objective:** public, verified deployment (Render API + Vercel SPA) and a README that lets judges understand and run the project.
**Prompts:** [18-deployment](../prompts/18-deployment.md), [20-documentation](../prompts/20-documentation.md) · **Branch:** `chore/release` · **Depends on:** Phase 5 core journey working (deploy can start once sample mode works end to end) · **Skill:** `/deployment-release` (manual)

## Acceptance checks
- [ ] `GET <api>/api/health` returns ok. The sample journey works on the owner's phone over mobile data.
- [ ] One owner-approved live run works in production.
- [ ] No key in the frontend bundle. CORS restricted to the Vercel URL.
- [ ] README reproducible from a fresh clone (mock mode, no key). Licence present. Screenshots linked.
- [ ] Release row added to [RUNBOOK](../RUNBOOK.md).
