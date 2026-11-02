---
name: frontend-engineering
description: Procedures for building GlowCue's React + TypeScript + Tailwind v4 interface. Covers pages, components, design tokens, API calls, session and cart state, image preparation, forms, the loading/error/empty states, accessibility and responsive behaviour. Use when creating or changing anything under frontend/.
paths: "frontend/**"
---

# Frontend Engineering

Rules: `.claude/rules/frontend.md` (auto-loaded). Design: `docs/DESIGN_SYSTEM.md`. Contracts: `docs/API_CONTRACTS.md`.

## Prerequisites
Run `cd frontend && npm install` once. The backend runs in mock mode on :8000 and `frontend/.env.local` has `VITE_API_BASE_URL=http://localhost:8000`.

## Procedure: build a page
1. Read the screen row in `docs/DESIGN_SYSTEM.md` §8.3 (purpose, components, interactions, states).
2. List the components it needs. Reuse existing ones in `src/components/`, and create a new one only if no existing one fits.
3. Add or extend the typed API functions in `src/lib/api.ts`. Pages never call `fetch` directly.
4. Build the page in `src/pages/` with all three states: loading, error and empty.
5. Register the route in `src/App.tsx`.
6. Check the page at 375, 768 and 1280 px in the dev server, and do a keyboard-only pass.
7. Run `npm run lint && npm run typecheck && npm run build`.

## Procedure: build a component
Use typed props and no data fetching. Style with token-based Tailwind classes. Accessible names are required for icon buttons. Keep each component small, ideally under ~150 lines; split it if it grows.

## Image preparation (`lib/imagePrep.ts`)
1. Accept `image/jpeg` and `image/png`, under 10 MB.
2. Decode with `createImageBitmap(file, { imageOrientation: "from-image" })`.
3. Reject images whose short side is under 480 px.
4. Scale so the long side is at most 2048 px.
5. Re-encode with `canvas.toBlob("image/jpeg", 0.9)`. This strips EXIF.

## Quality checks
- [ ] No `any`, no hex colours, no `fetch` outside `lib/api.ts`.
- [ ] `aria-live` on progress, visible focus, AA contrast, tap targets ≥ 44 px.
- [ ] Sample badge and demo labels shown where required. Cosmetic copy only.
- [ ] Lint, typecheck and build all green.

## Output and completion
The page or component works in mock mode, looks right at three widths, and the build is green. Then hand over to `/design-review` or Antigravity at the end of a UI phase.
