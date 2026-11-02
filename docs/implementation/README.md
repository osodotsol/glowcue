# Implementation phases and verification gates

Each phase has one gate document. A phase is **done** only when its gate's acceptance checks pass with evidence recorded in [PROJECT_STATUS](../PROJECT_STATUS.md). Timing is in [IMPLEMENTATION_ROADMAP §18](../IMPLEMENTATION_ROADMAP.md).

| Phase | Gate doc | Prompts | Branch | PR | Planned window (WAT) |
|---|---|---|---|---|---|
| 0 Foundation | [PHASE_0_FOUNDATION](PHASE_0_FOUNDATION.md) | 01 | `chore/project-foundation` | PR #1 | Sat 17:30–19:00 |
| 1 Backend core | [PHASE_1_BACKEND](PHASE_1_BACKEND.md) | 02 | `feat/backend-api` | PR #2 | Sat 19:00–20:00 |
| 2 YouCam API | [PHASE_2_API](PHASE_2_API.md) | 03, 04 | `feat/youcam-integration` | PR #3 | Sat 20:00–21:30 |
| 3 Engine | [PHASE_3_ENGINE](PHASE_3_ENGINE.md) | 05, 06, 07 | `feat/recommendation-engine` | PR #4 | Sat 21:30 → Sun 08:00 |
| 4 Frontend | [PHASE_4_FRONTEND](PHASE_4_FRONTEND.md) | 08–14 | `feat/frontend-experience`, `feat/shopping-cart` | PR #5, #6 | Sun 08:00–17:30 |
| 5 Integration & QA | [PHASE_5_INTEGRATION_QA](PHASE_5_INTEGRATION_QA.md) | 15, 16, 17 | `feat/integration`, `test/end-to-end` | PR #7 | Sun 17:30–23:00 |
| 6 Release | [PHASE_6_RELEASE](PHASE_6_RELEASE.md) | 18, 20 | `chore/release` | PR #8 | Sun 19:30–21:00 (deploy) · Mon 06:30–08:00 (docs) |
| 7 Submission | [PHASE_7_SUBMISSION](PHASE_7_SUBMISSION.md) | 21, 22 | `docs/submission` | PR #9 | Mon 08:00–14:00 |

Prompt 19 (GitHub PR creation) applies at the end of every phase through the `/pr-workflow` skill.

**Phase ordering differs slightly from the blueprint's Phases 0–13:** the blueprint's Phases 1 and 3 (definition and architecture) are complete, absorbed into Phase 0 and the docs. Deployment (Phase 6) intentionally overlaps Phase 5, because we deploy *before* polishing.
