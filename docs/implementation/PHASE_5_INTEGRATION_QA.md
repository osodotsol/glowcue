# Phase 5: Integration, testing and security

**Objective:** a real selfie goes all the way to checkout in live mode locally; the e2e smoke test protects the journey; a security review passes.
**Prompts:** [15-frontend-backend-integration](../prompts/15-frontend-backend-integration.md), [16-testing](../prompts/16-testing.md), [17-security-review](../prompts/17-security-review.md) · **Branches:** `feat/integration`, `test/end-to-end` · **Depends on:** Phases 2–4 · **Skills:** `/test-and-verify`, `/security-review` · **Reviewers:** `qa-engineer`, `security-reviewer`

## Acceptance checks
- [ ] One owner-approved live run (≤ 2 runs, ≤ 28 units) reaches checkout. Unit delta recorded.
- [ ] Each YouCam error path shows its UI state (verified with mocks and deliberately bad images).
- [ ] Playwright smoke test (mock mode) green. Full test matrix green.
- [ ] Security review: zero High findings. Report in `docs/qa/`.
- [ ] **Feature freeze at Sun 21:00 WAT.** After that, only fixes.
