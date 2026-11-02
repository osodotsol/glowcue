# Implementation prompts

One prompt per task, numbered in **execution order**. The easiest way to run one is `/phase-execution docs/prompts/NN-name.md`. That skill loads the prompt, the rules and the gate, and produces the standard completion report.

If you paste a prompt manually instead, prefix it with the **standard header**:

> You are implementing GlowCue. Follow `CLAUDE.md`, `AGENTS.md` and the path rules in `.claude/rules/`. Read the documents cited under *Context* before coding. Work on the branch named in the prompt, never on `main`. Mock mode is the default; **make no live YouCam calls unless this prompt says so and the owner approves in chat**. Never read `.env` files or print secrets. Touch only the files under *Expected files* unless strictly necessary, and explain any exception. Finish with the completion report defined in `/phase-execution` and update `docs/PROJECT_STATUS.md`.

Every prompt has the same sections: Objective · Context · Instructions · Expected files · Constraints · Acceptance criteria · Required tests · Definition of completion.

| # | Prompt | Phase | Branch |
|---|---|---|---|
| 01 | [Project foundation](01-project-foundation.md) | 0 | `chore/project-foundation` |
| 02 | [Backend architecture](02-backend-architecture.md) | 1 | `feat/backend-api` |
| 03 | [YouCam API integration + live probe](03-youcam-api-integration.md) | 2 | `feat/youcam-integration` |
| 04 | [Response normalisation + sample fixture](04-response-normalization.md) | 2 | `feat/youcam-integration` |
| 05 | [Product catalogue](05-product-catalogue.md) | 3 | `feat/recommendation-engine` |
| 06 | [Recommendation engine](06-recommendation-engine.md) | 3 | `feat/recommendation-engine` |
| 07 | [Routine builder](07-routine-builder.md) | 3 | `feat/recommendation-engine` |
| 08 | [Frontend design system](08-frontend-design-system.md) | 4 | `feat/frontend-experience` |
| 09 | [Landing page](09-landing-page.md) | 4 | `feat/frontend-experience` |
| 10 | [Image upload & consent](10-image-upload.md) | 4 | `feat/frontend-experience` |
| 11 | [Analysis interface (processing + results)](11-analysis-interface.md) | 4 | `feat/frontend-experience` |
| 12 | [Heatmaps](12-heatmaps.md) | 4 | `feat/frontend-experience` |
| 13 | [Product recommendations & routine](13-product-recommendations.md) | 4 | `feat/shopping-cart` |
| 14 | [Cart & checkout preview](14-cart.md) | 4 | `feat/shopping-cart` |
| 15 | [Frontend/backend integration](15-frontend-backend-integration.md) | 5 | `feat/integration` |
| 16 | [Testing](16-testing.md) | 5 | `test/end-to-end` |
| 17 | [Security review](17-security-review.md) | 5 | `fix/security-*` (if needed) |
| 18 | [Deployment](18-deployment.md) | 6 | `chore/release` |
| 19 | [GitHub PR creation](19-github-pr-creation.md) | every phase | current branch |
| 20 | [Documentation / README](20-documentation.md) | 6 | `chore/release` |
| 21 | [Demo production (screenshots + video script)](21-demo-production.md) | 7 | `docs/submission` |
| 22 | [Devpost submission](22-devpost-submission.md) | 7 | `docs/submission` |
