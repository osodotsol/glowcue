# 14: Cart and checkout preview

**Branch:** `feat/shopping-cart` · **Phase:** 4 · **Skill:** `/frontend-engineering` · **Depends on:** 13, 05

## Objective
A transparent cart and a checkout preview that close the shopping loop, plus a one-tap "clear my data".

## Context
`docs/DESIGN_SYSTEM.md` §8.3 (Cart and Checkout rows), `docs/PRD.md` F10–F11, `docs/API_CONTRACTS.md` (`/api/cart/quote`).

## Instructions
1. `state/CartContext.tsx`:
   - items `{product_id, qty}`;
   - `addRoutine(selected)`, `setQty`, `remove`, `clear`;
   - persisted to `sessionStorage` (ids and quantities only).
2. `pages/Cart.tsx`:
   - line items (image, name, price from the server quote, quantity stepper 1–5, remove);
   - subtotal from `POST /api/cart/quote`;
   - budget meter vs the chosen budget;
   - a "Routine complete ✓" indicator when every routine product is in the cart;
   - an empty state linking to Routine;
   - CTA **Preview checkout**.
3. `pages/Checkout.tsx`:
   - order summary;
   - a printable routine card (AM/PM steps) using `window.print()` with a print stylesheet;
   - a "Demo store — no payment is taken" notice;
   - **Start over & clear my data**, which clears the cart, session, preferences and analysis, then returns to Landing.
4. Header cart badge shows the item count.

## Expected files
`frontend/src/state/CartContext.tsx`, `frontend/src/pages/{Cart.tsx,Checkout.tsx}`, `frontend/src/index.css` (print styles).

## Constraints
No payment fields. The total always comes from the server.

## Acceptance criteria
Totals equal the server quote. A refresh keeps the cart. Clear-data leaves `sessionStorage` empty (verified in the report). Works at 375 and 1280 px.

## Required tests
Vitest for the cart reducer (add, qty bounds, remove, clear). Lint, typecheck and build.

## Definition of completion
Report, then `/design-review`, then the `feat/shopping-cart` PR via prompt 19.
