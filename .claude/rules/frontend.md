---
paths:
  - "frontend/**"
---
# Frontend rules (React / TypeScript / Tailwind v4)

## Structure (`frontend/src/`)
- `pages/` holds one component per route: Landing, Analyze, Processing, Results, Routine, Cart, Checkout, NotFound.
- `components/` holds reusable, presentational components that receive props, call no APIs and use design tokens.
- `lib/api.ts` is the **only** place that calls `fetch`. It's typed with `lib/types.ts` and reads the base URL from `import.meta.env.VITE_API_BASE_URL`.
- `lib/imagePrep.ts` does client-side validation, resizing (long side ≤ 2048 px) and EXIF stripping.
- `state/` contains the React contexts (session, cart). Persist only ids, quantities and preferences to `sessionStorage`, **never images or masks**.

## Standards
- TypeScript runs in `strict` mode. No `any` without a comment explaining why. Props are typed with interfaces.
- Style with Tailwind utilities driven by the theme tokens in `src/index.css` (`@theme`). No hard-coded hex colours in components.
- Every async view has three states: **loading** (a skeleton or progress with `aria-live="polite"`), **error** (friendly message plus a recovery action) and **empty**.
- Accessibility:
  - semantic HTML and labelled inputs;
  - visible focus;
  - tap targets ≥ 44 px;
  - WCAG AA contrast;
  - heatmap information always available as text too;
  - `prefers-reduced-motion` respected.
- Design mobile-first and verify at 375, 768 and 1280 px.
- No secrets or `VITE_*` keys other than the public API base URL.
- Show the **"Recorded sample"** badge whenever `mode === "sample"`, and the demo-catalogue label on every product.

## Commands
```bash
cd frontend && npm run dev        # http://localhost:5173
cd frontend && npm run lint && npm run typecheck && npm run build
```
