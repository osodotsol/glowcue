# 13: Product recommendations and routine page

**Branch:** `feat/shopping-cart` · **Phase:** 4 · **Skill:** `/frontend-engineering` · **Depends on:** 06, 07, 11

## Objective
The core decision screen: preferences (budget, shelf check, filters, routine size) driving the optimised AM/PM routine, with receipts, swaps, totals and warnings.

## Context
`docs/DESIGN_SYSTEM.md` §8.3 (Routine and Product drawer rows), `docs/PRD.md` F7–F9, `docs/API_CONTRACTS.md` (`/api/recommendations`), `docs/RECOMMENDATION_ENGINE.md` §9.2.

## Instructions
1. `pages/Routine.tsx`:
   - **Preferences panel** (collapsible on mobile):
     - budget slider using the ₦ range from `/api/config`;
     - "I already own" chips (cleanser, moisturiser, sunscreen, serum, eye);
     - fragrance-free and sensitive-skin toggles;
     - routine size (Minimal, Balanced, Complete).

     Debounce changes by 300 ms, then call `POST /api/recommendations` with metrics (scores only) and preferences.
   - **Summary bar** (sticky at the bottom on mobile): coverage %, product count, total vs budget, budget meter.
   - **AM/PM toggle** → `RoutineTimeline` of steps. Each step shows a `ProductCard`: image, name, "GlowCue Demo" label, price, key ingredient, **Why this?** expanding the receipts, **Swap** opening a drawer of alternatives, **Details** opening the product drawer.
   - **Warnings and unaddressed concerns** banners. Infeasible budget → a banner with "Increase budget to ₦X" (sets the slider) and a "Mark items you own" hint.
   - CTA **Add routine to cart**.
2. Swap is client-side state, re-quoting the total through `/api/cart/quote`, or re-calling recommendations with a pinned product if the engine supports it. Choose the simpler path and document it.
3. Persist preferences (not images) to `sessionStorage`.

## Expected files
`frontend/src/pages/Routine.tsx`, `frontend/src/components/{ProductCard.tsx,RoutineTimeline.tsx,ReceiptList.tsx,BudgetMeter.tsx,PreferencesPanel.tsx,ProductDrawer.tsx}`, `frontend/src/lib/api.ts`.

## Constraints
Prices always come from server responses. Cosmetic copy only. No more than one primary action per viewport.

## Acceptance criteria
With sample data, changing the budget or owned items visibly changes the routine and total within 1 s. Every product shows at least one receipt. The infeasible-budget path works. Layout works at 375 and 1280 px.

## Required tests
Vitest for any pure helpers (formatting ₦, debounce wrapper). Lint, typecheck and build. Manual journey check.

## Definition of completion
Report with screenshots or notes. Then `/design-review`.
