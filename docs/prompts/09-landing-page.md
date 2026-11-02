# 09: Landing page

**Branch:** `feat/frontend-experience` · **Phase:** 4 · **Skill:** `/frontend-engineering` · **Depends on:** 08

## Objective
A premium, trustworthy landing page that explains GlowCue's value in five seconds and starts either path.

## Context
`docs/DESIGN_SYSTEM.md` §8.3 (Landing row), `docs/PRODUCT_BRIEF.md` §1 (differentiators), `docs/PRD.md` F1.

## Instructions
1. Hero section:
   - H1 "Know your skin. Choose with confidence."
   - Sub-line "The smallest routine that covers your skin — within your budget, without re-buying what you own."
   - Primary CTA **Analyse my selfie** (`/analyze`) and secondary **Try a recorded sample** (fetches the sample, then `/results`).
2. A 3-step strip (Analyse → Understand → Shop smart). A row of 3 differentiators (budget optimiser, shelf check, honest scores and receipts). Privacy and "cosmetic, not medical" notes.
3. On mount, call `GET /api/health`. If there's no answer within 3 s, show a subtle "Waking the analysis server…" note. The sample CTA still works once the server responds.
4. `lib/api.ts`: add `getHealth`, `getConfig` and `getSampleAnalysis`. `state/SessionContext.tsx` holds the analysis result in memory.

## Expected files
`frontend/src/pages/Landing.tsx`, `frontend/src/lib/api.ts`, `frontend/src/state/SessionContext.tsx`.

## Constraints
No stock photos and no third-party logos. Copy is cosmetic and warm.

## Acceptance criteria
Above the fold shows the H1, both CTAs and the trust line at 375 px. The sample CTA lands on Results with data (once prompt 11 exists, or a stub). Lighthouse accessibility ≥ 95.

## Required tests
Lint, typecheck and build. A manual check at 3 viewports.

## Definition of completion
Report with notes on the viewport checks.
