# Personal Preparation Checklist (owner tasks)

> **Status:** planned design from the GlowCue blueprint (research snapshot 31 Oct 2026). Nothing here is implemented unless [PROJECT_STATUS](PROJECT_STATUS.md) says so. Tags: **[V]** verified, **[A]** assumption, **[R]** recommendation, **[U]** unresolved.

## 20. Personal preparation checklist

| Cat | Item | Why | Where | Free? | Before coding? | Agent can help? |
|---|---|---|---|---|---|---|
| A | Devpost account + Join hackathon | Entry + redeem code | [devpost](https://youcam-api-skin-ai-ecommerce.devpost.com/) | Yes | **Yes** | No |
| A | YouCam API account | API access | [yce.perfectcorp.com/ai-api](https://yce.perfectcorp.com/ai-api) | Yes | **Yes** | No |
| A | GitHub account + empty public repo `glowcue` | Code hosting | github.com | Yes | Yes | Claude Code can push once the remote exists |
| A | Render + Vercel accounts (GitHub login) | Hosting | render.com, vercel.com | Yes | By Sun 19:00 | Steps given by Claude Code |
| A | YouTube channel | Video | youtube.com | Yes | By Mon 08:00 | No |
| B | Redeem code → 1,000 units | Credits | Email + console | Yes | **Yes** | No |
| B | API key (store in a password manager) | Auth | Console → API Keys | Yes | **Yes** | No. **Never paste it into chat;** type it into `.env` yourself. |
| C | Python ✓, Node ✓, Git ✓ (already installed) | Dev | — | Yes | Done | — |
| C | VS Code + Claude Code ✓, Antigravity ✓ | Dev | — | Yes | Done | — |
| C | OBS Studio or Snipping Tool; Clipchamp | Video | obsproject.com / built into Windows | Yes | By Mon | No |
| C | Playwright browsers | e2e + screenshots | `npx playwright install` | Yes | Phase 6 | Claude Code |
| D | 2–3 test selfies (good light, front-facing, hair off forehead, face > 60% width, ≥ 1080 px tall) | Probe + demo | Your phone | Yes | **Yes** | No |
| D | 3 "bad" test images (tiny, dark, no face) | Error tests | Anything | Yes | Phase 6 | Claude Code can generate synthetic ones |
| D | Logo, product SVGs | Brand | — | Yes | No | **Claude Code** |
| E | Understand: async polling, env vars, CORS, raw vs ui score | Debug confidence | [§6](YOUCAM_API.md)–7 | — | Skim | Ask Claude Code to explain any |
| G | `backend/.env` with `YOUCAM_API_KEY` (typed by you) | Secrets | — | — | Phase 2 | Claude Code creates `.env.example` |
| H | YouCam API, Google Fonts, Lucide | Runtime deps | — | Yes | — | Claude Code |
| I | Repo public, README, 4+ screenshots, YouTube public video, Devpost fields | Submission | — | Yes | Mon | Claude Code drafts text and screenshots |

### F. Decisions you must make (please answer before Phase 1)

| # | Decision | Options | My recommendation & consequence |
|---|---|---|---|
| **F1** | Positioning & currency | (a) Global, USD; (b) **Budget-first shoppers, launching in Nigeria, NGN + "no-bleach promise"** | **(b).** A more specific and credible Impact story, and a differentiator. The cost is NGN-only prices; judges still understand. |
| **F2** | Catalogue type | (a) **Fictional labelled demo**; (b) real products | **(a).** Avoids trademark issues in the video and unverifiable prices. |
| **F3** | Sample-mode photo | (a) **Your own selfie, published in the repo/app**; (b) a consenting friend with written consent; (c) sample shows masks and scores but **no photo** (masks over a neutral silhouette) | (a) if you're comfortable, since it's the best demo. (c) is the most private but a weaker visual. |
| **F4** | Rising Star / Women in Tech eligibility | Are you an enrolled student with a school-issued email? Does any team member self-identify as a woman? | Opt in only if eligible. False info means disqualification. |
| **F5** | Delete YouCam task after results | (a) **Yes, if verified in Phase 2**; (b) no | (a). A strong privacy claim. |
| **F6** | Team / submitter type | Individual or team | Affects the Devpost form and prize payout. |

---
