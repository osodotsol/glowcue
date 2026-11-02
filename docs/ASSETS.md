# Visual assets register

Where every image GlowCue shows comes from, what it may be used for, and how to replace it.
Rule: no image ships publicly unless its row says **cleared**.

## 1. Product and texture renders (cleared, original)
| Files | Source | Rights | Notes |
|---|---|---|---|
| `frontend/public/products/gc-*.webp` (15 packshots) | Generated procedurally by `scripts/assets/render_products.py` (numpy + Pillow), 31 Oct 2026 | Original work made for GlowCue; no third-party content, no real brands, no faces | Fictional "GlowCue Demo" products. WebP, about 15–25 KB each |
| `frontend/public/products/scenes/*.webp` (hero still life, evening still life, coral gel, cream swirl, droplets) | Same generator | Same | Used for storytelling tiles, the morning/evening ritual headers and the demo-profile "skin stories" |

Regenerate: `python scripts/assets/render_products.py <out_dir>`, then convert to WebP (quality 80) into `frontend/public/products/`.
The repo's photo rule (`scripts/security/secret_patterns.py`, `PHOTO_ALLOWED_PREFIXES`) allows images only under `frontend/public/products/`.

## 2. Brand portraits (TEMPORARY, not cleared)
| Slot | Local file (git-ignored) | Used in | Status |
|---|---|---|---|
| P1 hero film | `frontend/public/private/videos/glowcue-hero.mp4`, plus `glowcue-hero-poster.webp` (frame at 0.1 s, the poster and reduced-motion still) and `glowcue-hero-still.webp` (frame at 9.9 s, spare) | Landing hero (desktop arch, mobile opening), muted, looping and inline | **Temporary.** Owner-supplied AI-generated clip; generator terms and licence **not verified** |
| P1 hero still (superseded) | `frontend/public/private/portraits/p1-hero.webp` | No longer shown; replaced by the film | **Temporary.** Owner-supplied screenshot crop; source, licence and model release **not verified** |
| P2 consultation | `frontend/public/private/portraits/p2-consultation.webp` (previous image kept as `p2-consultation.prev.webp`) | About-you consultation (mobile stage-1 band, desktop side panel) | **Temporary**, as above. Replaced 1 Nov with an owner upload, the same photograph the superseded P1 still came from |
| P3 storytelling | `frontend/public/private/portraits/p3-storytelling.webp` | Landing "Meet your edition" tall tile | **Temporary**, as above |

**Production builds never contain these files (Phase D1, 1 Nov 2026):**
- `USE_PRIVATE_ASSETS` in `frontend/src/components/ui.tsx` is `import.meta.env.DEV`. Production builds therefore never reference the private files; even the file names are removed.
- In production each slot shows a cleared GlowCue Demo studio render instead, with alt text describing the render:
  - hero film → `scenes/hero_still`;
  - consultation portrait → `scenes/cream_swirl`;
  - storytelling portrait → `scenes/gel_coral`.
- The temporary-photo notes and developer placeholders appear only in development.
- A Vite plugin in `frontend/vite.config.ts` deletes `dist/private/` after every build.
- `frontend/scripts/check-build-assets.mjs` runs as part of `npm run build` and fails the build if any private path, file name or reference remains in `dist/`.

Rules while temporary:
- The folder matches `private/` in `.gitignore` and the pre-commit forbidden-path rule, so these files are never committed or pushed.
- Local development and private demos only. Not for the public deployment, the Devpost video or screenshots, or any shared material.
- They are brand imagery only: never placed beside or over scores, never presented as a customer or an analysed face.
- In development, if a file is missing (for example in a fresh clone), `Portrait` and `HeroVideo` show a labelled placeholder naming the file and folder. Production never shows it.

Hero film facts (inspected 1 Nov 2026): H.264, 1280×720, 10.05 s, 30 fps, about 1 Mbit/s, 1.24 MB, with an AAC audio track (always muted in the page). The source has **baked-in white side bars** (130 px on the left, about 34 px on the right). `HeroVideo` crops to the real 1116×720 picture, so the bars never show. A replacement film without bars needs the crop removed (the `aspectRatio` and the 114.7% / -11.65% offsets in `HeroVideo`). Under `prefers-reduced-motion` the poster still is shown instead of the film.

### Replacing them with cleared photographs
1. Obtain three distinct, properly licensed photographs (or original AI-generated portraits under commercial terms) matching the briefs in the design canvas (board 02b): P1 deep skin tone, P2 medium-tan, P3 light-medium with freckles.
2. Record each one in the table below before use.
3. Export WebP at about 1600 px on the long edge and save with the same file names. No code change is needed.
4. If they may be committed, move them to an allowed, non-ignored folder, update the `Portrait` component's path, and change the status here to **cleared**.

| Slot | Source URL | Asset ID | Contributor | Licence | Model release | Attribution required |
|---|---|---|---|---|---|---|
| P1 | — | — | — | — | — | — |
| P2 | — | — | — | — | — | — |
| P3 | — | — | — | — | — | — |

## 3. Fonts (cleared)
Fraunces and Inter, self-hosted through `@fontsource-variable/fraunces` and `@fontsource-variable/inter` (SIL Open Font License 1.1).
