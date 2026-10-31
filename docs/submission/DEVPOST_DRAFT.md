# Devpost Submission Draft

> **Status:** planned design from the GlowCue blueprint (research snapshot 31 Oct 2026). Nothing here is implemented unless [PROJECT_STATUS](../PROJECT_STATUS.md) says so. Tags: **[V]** verified, **[A]** assumption, **[R]** recommendation, **[U]** unresolved.

## 17. Devpost submission strategy

**Fields known [V] / expected [A]:**

| Field | Status |
|---|---|
| Project name, elevator pitch | [A] standard Devpost |
| Thumbnail | [A] standard Devpost |
| "About the project" story | [A] standard Devpost |
| Built with | [A] standard Devpost |
| Try-it-out links | [A] standard Devpost |
| Image gallery | [A] standard Devpost |
| Video URL | [V] required |
| Repo URL | [V] required |
| Text description | [V] required |
| Screenshots | [V] required |
| Submitter type: Individual / Team / Organisation | [A], inferred from gallery filters |
| App status: New / Existing & Enhanced | [A], inferred from gallery filters |
| Special-award opt-ins: Women in Tech / Rising Star with school email | [V] |
| Testing instructions | [A] |

**Confirm the exact list when you open the draft in Phase 0.**

**Draft content:**
- **Title:** GlowCue
- **Tagline (≤ 200 chars):** "Know your skin. Choose with confidence. GlowCue turns YouCam skin analysis into the smallest, budget-fitting skincare routine, skipping what you already own."
- **Inspiration:** the "standing in the aisle" moment; overspending; the case for honest and safe advice in budget markets (cite WHO 2023 if Nigeria positioning is chosen).
- **What it does:** the journey, with bullets on the four differentiators.
- **How we built it:** FastAPI + React; YouCam v2.1 SD File → Task → Poll flow; normaliser; exhaustive optimiser; Render + Vercel; N tests.
- **How YouCam is used:** endpoints, the 10 concerns, raw vs ui score, masks with alpha overlay, task deletion, credit guard, recorded-sample mode (organiser-approved).
- **Challenges:** score semantics, mask alignment, protecting credits on a public demo, privacy.
- **Accomplishments / learned:** explainability, honest-score design.
- **Impact:** shoppers spend less and buy fewer redundant products; retailers get higher-trust conversion and fewer returns; safe-catalogue policy.
- **What's next:** a real retailer catalogue feed, makeup/foundation VTO from the same selfie, progress re-scans, NGN payments.
- **Testing instructions:** "Open <URL>, click *Try a recorded sample* (a real, recorded YouCam result, no upload needed). Live selfie analysis is also enabled (daily limits apply). The first load may take ~45 s while the free server wakes."

---
