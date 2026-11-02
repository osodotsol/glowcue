# ADR-003: Product catalogue and market positioning

- **Status:** Accepted as **provisional default**, 31 Oct 2026. The owner may revise it before Phase 3.

## Context
Recommendations need a product catalogue. The demo video must not show third-party trademarks without permission [V rules]. Real Nigerian prices and ingredient lists can't be verified in time. The judges reward a "credible, specific case for a real audience".

## Options considered
| Option | Assessment |
|---|---|
| Real branded products | Trademark risk in the video. Prices and INCI lists can't be verified. |
| **Fictional "GlowCue Demo" products using real, common cosmetic ingredients** | No trademark issue, honest labelling, and the schema is ready for a real feed later |
| Global positioning with USD | Generic, a weaker impact story |
| **Nigeria-first, NGN, plus a "no-bleach promise"** | Specific audience. A WHO AFRO 2023 fact sheet cites high skin-lightening use and mercury risk, which supports the safety angle. |

## Decision
- 15 fictional products (`brand: "GlowCue Demo"`, `source: "fictional_demo"`), with illustrative ingredients and prices clearly labelled.
- Currency **NGN**. Nigeria-first copy, but the product isn't locked to Nigeria.
- Catalogue admission policy: no hydroquinone, mercury, steroids, or "whitening/bleaching" positioning, enforced by a test.
- Award eligibility and team composition are **not** asserted anywhere until the owner confirms them.

## Consequences
- Every product card, the README and the Devpost text carry the demo-catalogue disclaimer.
- Prices are illustrative. Cart totals are accurate *for the demo catalogue only*.
- Switching to USD or global later means changing a config value plus copy, not the code.
