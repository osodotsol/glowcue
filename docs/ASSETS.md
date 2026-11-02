# Visual assets register

Where every image GlowCue shows comes from, what it may be used for, and how to replace it.
Rule: no image ships publicly unless its row says **cleared**, or the owner has recorded an explicit exception in section 2.

## 1. Product and texture renders (cleared, original)
| Files | Source | Rights | Notes |
|---|---|---|---|
| `frontend/public/products/gc-*.webp` (15 packshots) | Generated procedurally by `scripts/assets/render_products.py` (numpy + Pillow), 31 Oct 2026 | Original work made for GlowCue; no third-party content, no real brands, no faces | Fictional "GlowCue Demo" products. WebP, about 15–25 KB each |
| `frontend/public/products/scenes/*.webp` (hero still life, evening still life, coral gel, cream swirl, droplets) | Same generator | Same | Used for storytelling tiles, the morning/evening ritual headers and the demo-profile "skin stories" |

Regenerate: `python scripts/assets/render_products.py <out_dir>`, then convert to WebP (quality 80) into `frontend/public/products/`.
The repo's photo rule (`scripts/security/secret_patterns.py`, `PHOTO_ALLOWED_PREFIXES`) allows images only under `frontend/public/products/`.

## 2. Brand portraits and hero film (published by owner decision; licence NOT verified)
| Slot | File | Used in | Status |
|---|---|---|---|
| P1 hero film | `frontend/public/brand/videos/glowcue-hero.mp4`, plus `glowcue-hero-poster.webp` (frame at 0.1 s: the poster and the reduced-motion still) | Landing hero (desktop arch, mobile opening), muted, looping and inline | **Published by owner decision (2 Nov 2026). Licence not verified.** Owner-supplied AI-generated clip; generator terms and licence unverified |
| P2 consultation | `frontend/public/brand/portraits/p2-consultation.webp` | About-you consultation (mobile stage-1 band, desktop side panel) | **Published by owner decision (2 Nov 2026). Licence not verified.** Owner upload; source, licence and model release unverified |
| P3 storytelling | `frontend/public/brand/portraits/p3-storytelling.webp` | Landing "Meet your edition" tall tile | **Published by owner decision (2 Nov 2026). Licence not verified**, as above |
| Not published | `frontend/public/private/` (git-ignored): `p1-hero.webp` (superseded still), `p2-consultation.prev.webp` (previous image), `glowcue-hero-still.webp` (spare frame), plus the originals of the files above | Nothing | Kept locally only. Never referenced by the app and removed from `dist/` |

**What is published, and the guard around it (2 Nov 2026):**
- The four files in the first three rows were copied unchanged from `frontend/public/private/` to `frontend/public/brand/` and are served by the site. `Portrait` and `HeroVideo` in `frontend/src/components/ui.tsx` read them from `/brand/...` in development and production alike.
- If one of these files fails to load, its slot falls back to the matching GlowCue studio render (`scenes/hero_still`, `cream_swirl`, `gel_coral`), so the layout never breaks.
- `frontend/public/private/` is still git-ignored, is deleted from `dist/` by the Vite plugin in `frontend/vite.config.ts`, and is never referenced by the app.
- `frontend/scripts/check-build-assets.mjs` (run by `npm run build`) fails the build if any `private/` path or `/private/` reference reaches `dist/`, if `dist/brand/` contains any file other than the four approved ones, or if one of the four is missing.
- The repo's photo guard (`scripts/security/secret_patterns.py`) allows photographs under `frontend/public/products/`, `docs/screenshots/` and `.github/`, plus exactly these brand files (`PHOTO_ALLOWED_FILES`). Any other photograph in `frontend/public/brand/` is still refused by the pre-commit hook and the CI secret scan.

Rules for these images:
- They are brand imagery only: never placed beside or over scores, never presented as a customer or an analysed face.
- The licence status above stays **unverified** until the owner records the source, licence and model release in the table below. Do not describe them as cleared before then.

Hero film facts (inspected 1 Nov 2026): H.264, 1280×720, 10.05 s, 30 fps, about 1 Mbit/s, 1.24 MB, with an AAC audio track (always muted in the page). The source has **baked-in white side bars** (130 px on the left, about 34 px on the right). `HeroVideo` crops to the real 1116×720 picture, so the bars never show. A replacement film without bars needs the crop removed (the `aspectRatio` and the 114.7% / -11.65% offsets in `HeroVideo`). Under `prefers-reduced-motion` the poster still is shown instead of the film.

### Replacing them with cleared photographs
1. Obtain three distinct, properly licensed photographs (or original AI-generated portraits under commercial terms) matching the briefs in the design canvas (board 02b): P1 deep skin tone, P2 medium-tan, P3 light-medium with freckles.
2. Record each one in the table below before use.
3. Export WebP at about 1600 px on the long edge and save over the files in `frontend/public/brand/portraits/` with the same names. No code change is needed. If a file name changes, update `BRAND_FILES` in `frontend/scripts/check-build-assets.mjs` too.
4. Change the status in the table above to **cleared** only once the row below is filled in.

| Slot | Source URL | Asset ID | Contributor | Licence | Model release | Attribution required |
|---|---|---|---|---|---|---|
| P1 | — | — | — | — | — | — |
| P2 | — | — | — | — | — | — |
| P3 | — | — | — | — | — | — |

## 3. Fonts (cleared)
Fraunces and Inter, self-hosted through `@fontsource-variable/fraunces` and `@fontsource-variable/inter` (SIL Open Font License 1.1).
