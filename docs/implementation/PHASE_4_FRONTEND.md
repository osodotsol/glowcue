# Phase 4: Frontend experience and shopping

**Objective:** the complete customer journey UI in mock or sample mode: Landing → Analyse → Processing → Results with heatmaps → Routine → Cart → Checkout preview.
**Prompts:** [08](../prompts/08-frontend-design-system.md) design system · [09](../prompts/09-landing-page.md) landing · [10](../prompts/10-image-upload.md) upload and consent · [11](../prompts/11-analysis-interface.md) processing and results · [12](../prompts/12-heatmaps.md) heatmaps · [13](../prompts/13-product-recommendations.md) routine and recommendations · [14](../prompts/14-cart.md) cart and checkout
**Branches:** `feat/frontend-experience` (08–12) → PR · `feat/shopping-cart` (13–14) → PR · **Depends on:** Phase 1 contracts (Phase 3 for 13–14) · **Skills:** `/frontend-engineering`, `/design-review`

## Acceptance checks
- [ ] Full journey works in sample mode at 375 / 768 / 1280 px, with no console errors.
- [ ] Every async view has loading, error and empty states. Keyboard-only run succeeds.
- [ ] Antigravity report (AG-REPORT) has no open P0/P1. `frontend-reviewer` verdict is not "CHANGES REQUIRED".
- [ ] Lint, typecheck and build green.

## Cut order if late
Product drawer → swap → camera capture → per-concern heatmap chips (keep one overlay toggle).
