---
name: design-review
description: Reviews GlowCue's consumer UI against the design system and the shopping journey. Covers visual hierarchy, typography, spacing, colour tokens, component consistency, responsive behaviour (375/768/1280 px), accessibility and checkout friction. Produces a ranked findings report and the hand-off prompt for Antigravity browser review. Use after finishing a UI page or phase, before a frontend PR, or when the owner asks how the app looks.
argument-hint: "[page or flow, default: full journey]"
---

# Design Review

References: `docs/DESIGN_SYSTEM.md` (tokens §8.1, flow §8.2, screens §8.3), `docs/WORKFLOW.md` (the Antigravity protocol).

## Prerequisites
The app runs locally in mock mode (backend :8000, frontend :5173). The work is committed, giving Antigravity a clean checkpoint.

## Procedure
1. **Static pass (Claude):** delegate to the `frontend-reviewer` subagent with the page list. It reads the code and checks:
   - token usage and hard-coded colours;
   - state coverage (loading, error, empty);
   - accessibility semantics;
   - copy tone and the cosmetic-claim rules;
   - sample and demo labels.
2. **Browser pass:** run the Antigravity review prompt in `docs/WORKFLOW.md` §11.3 at the checkpoint. Tell the owner the exact commit to review. Antigravity writes `docs/qa/AG-REPORT-<n>.md`. If Playwright is installed, Claude may also capture screenshots at 375, 768 and 1280 px into `docs/qa/screens/`.
3. **Merge findings** into one table: severity (P0 blocks the journey, P1 is visibly broken or inaccessible, P2 is polish, P3 is nice-to-have), screen, viewport, issue, fix proposal and effort.
4. **Rank by judging value.** Design is 25% of the score, so prioritise anything that breaks "complete, coherent product experience" first, then visual polish of Results and Routine.
5. **Hand over:** P0 and P1 fixes become a `fix/ui-*` task through `/phase-execution`. P2 and P3 go into the PROJECT_STATUS backlog.

## Checklist
- [ ] One clear primary action per screen. The stepper shows progress.
- [ ] Fraunces for headings and Inter for body, with a consistent type scale. 8-pt spacing. 16 px card radius.
- [ ] Only token colours, warm ivory background, sage primary, clay used for priority accents only.
- [ ] No horizontal scroll at 375 px. Sticky summary bar on mobile Routine.
- [ ] Heatmap is aligned and has an opacity control, a legend and a text equivalent.
- [ ] Receipts are readable. Totals are visible without scrolling on desktop.
- [ ] Focus is visible, tap targets ≥ 44 px, AA contrast, reduced motion respected.

## Output and completion
`docs/qa/DESIGN-REVIEW-<n>.md` with the ranked table and the owner-approved fix list.
