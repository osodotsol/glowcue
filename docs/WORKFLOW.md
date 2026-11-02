# Claude Code & Antigravity Workflow

> **Status:** planned design from the GlowCue blueprint (research snapshot 31 Oct 2026). Nothing here is implemented unless [PROJECT_STATUS](PROJECT_STATUS.md) says so. Tags: **[V]** verified, **[A]** assumption, **[R]** recommendation, **[U]** unresolved.

## 11. Claude Code & Antigravity workflow

### 11.1 Division of labour

| Area | Claude Code (writer) | Antigravity (reviewer) |
|---|---|---|
| Backend, engine, tests | Owns | Never edits |
| Frontend code | Owns | Never edits, except on an explicit `ag/*` branch for CSS-only fixes when Claude Code is idle |
| Browser checks at 375 / 768 / 1280 px, flow walkthroughs, screenshots of defects | Can run Playwright | **Owns.** Writes `docs/qa/AG-REPORT-<n>.md` |
| Docs | Owns | Owns `docs/qa/` only |

### 11.2 Conflict prevention
1. **One writer at a time.** Claude Code commits → you tag the checkpoint (`git tag cp-<phase>`) → Antigravity reviews the **running app** (read-only) → its report is committed → Claude Code fixes.
2. Before any handoff: `git status` must be clean.
3. If Antigravity ever edits, it works on branch `ag/<topic>` and **you** merge after Claude Code has stopped. Then Claude Code pulls before continuing.
4. Claude Code is told in each prompt: "Do not refactor files outside this task's list; do not rename public interfaces."
5. Decisions go in `docs/DECISIONS.md`, so neither agent re-litigates them.
6. Reverting is cheap: `git reset --hard cp-<phase>` (only you run this).

### 11.3 Antigravity review prompt (reuse each checkpoint)
> "Open http://localhost:5173 (or the deployed URL). Walk the full GlowCue journey twice: (1) 'Try a recorded sample', (2) upload `test_assets/selfie_ok.jpg`. Test at 375×812, 768×1024 and 1280×800. Check layout breaks, overflow, contrast, tap-target size (≥ 44 px), keyboard focus order, loading and error states, heatmap alignment, and copy consistency with 'cosmetic, not medical'. **Do not edit any files.** Write findings to `docs/qa/AG-REPORT-<n>.md` as a table: severity (P0–P3), screen, viewport, steps, expected, actual, screenshot path. End with your top 5 fixes ranked by visual and UX impact."

---
