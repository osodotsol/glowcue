# ADR-005: Demo analysis without the photo, and the Edition 2 frontend

- **Status:** Accepted, 1 Nov 2026 (owner authorised the Edition 2 implementation).

## Context
The first product slice needed a working journey before live YouCam analysis exists. The owner required that photos are never transmitted or persisted in mock mode, that demo results are never presented as a real analysis, and that the approved "Ritual Edition" design (Edition 2) be implemented without a full rewrite.

## Options considered
| Topic | Options | Choice |
|---|---|---|
| Mock analysis input | Upload the photo to a mock endpoint · keep the photo in the browser and choose a labelled demo profile | **Photo stays in the browser.** `POST /api/analyses/demo` takes a profile id only and rejects extra fields |
| Headline score | Average of the nine scores · count of attributes per band | **Count per band.** Averaging separate scales has no verified meaning |
| Navigation | Add a router library · hash-based navigation in app state | **Hash navigation** (`#/about/2`, `#/routine`): Back, Forward and reload work with no new dependency |
| Fonts | Google Fonts link · self-hosted variable fonts | **Self-hosted** `@fontsource-variable/fraunces` and `inter` (OFL), no third-party font requests |
| Motion | Animation library · CSS plus browser APIs | **CSS keyframes, View Transitions and Web Animations**; everything off under `prefers-reduced-motion` |
| Product imagery | Stock packshots · original renders | **Original procedural renders** (`scripts/assets/render_products.py`), owned outright |

## Decision
The choices marked above. Portraits are temporary owner-supplied files kept out of git ([ASSETS.md](../ASSETS.md)) until cleared photographs replace them.

## Consequences
- A live provider must later implement the same `SkinAnalysisProvider` interface and real upload, consent and limits (Phase 2).
- The report shows no face map in demo mode. Masks appear only from real live analysis.
- New frontend dependencies: two font packages only.
