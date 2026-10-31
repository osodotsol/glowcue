# 08: Frontend design system and app shell

**Branch:** `feat/frontend-experience` · **Phase:** 4 · **Skill:** `/frontend-engineering` · **Depends on:** 01

## Objective
Establish GlowCue's visual language as code: Tailwind v4 theme tokens, fonts, core components and the app shell with routing.

## Context
`docs/DESIGN_SYSTEM.md` §8.1–8.2 and §8.4, `.claude/rules/frontend.md`.

## Instructions
1. `src/index.css`: `@import "tailwindcss";` plus a `@theme` block with the colour tokens:

   | Token | Value |
   |---|---|
   | bg | #F7F3EE |
   | surface | #FFFFFF |
   | ink | #1F1D1B |
   | muted | #6B645C |
   | sage | #5E7A64 |
   | sage-soft | #E4EBE3 |
   | clay | #C47F5A |
   | line | #E7E0D7 |

   Also add the fonts (Fraunces for display, Inter for body, via Google Fonts `<link>` in `index.html` with `display=swap`), a 16 px card radius and a focus-ring style.
2. Install `react-router-dom` and `lucide-react` (ask before installing). Routes: `/`, `/analyze`, `/processing/:id`, `/results`, `/routine`, `/cart`, `/checkout`, `*`, plus a dev-only `/styleguide`.
3. Components in `src/components/`: `Button` (primary, secondary, ghost; loading state), `Card`, `Badge` (sample, demo, band), `ScoreBar` (raw score, "higher is better" label), `Stepper`, `Disclaimer`, `ErrorState`, `Skeleton`, `Drawer` (focus-trapped, Esc closes), `AppShell` (header with SVG wordmark logo and cart count; footer with disclaimer, privacy note and "Powered by YouCam AI Skin Analysis").
4. Logo: an SVG wordmark "GlowCue" in `src/assets/logo.svg`, plus `public/favicon.svg`.
5. `/styleguide` renders every component and state.

## Expected files
`frontend/src/{index.css,App.tsx,main.tsx}`, `frontend/src/components/*.tsx`, `frontend/src/pages/Styleguide.tsx`, `frontend/src/assets/logo.svg`, `frontend/public/favicon.svg`, `frontend/index.html`, `frontend/package.json`.

## Constraints
No hex colours outside the `@theme` block. Respect `prefers-reduced-motion`. WCAG AA contrast (`muted` on `bg` must pass, so verify it).

## Acceptance criteria
The styleguide renders at 375 and 1280 px without overflow. Keyboard focus is visible on every interactive element. Lint, typecheck and build green.

## Required tests
Lint, typecheck and build. (Vitest is added in prompt 10.)

## Definition of completion
Styleguide screenshot or description in the report. Run `/design-review` (static pass).
