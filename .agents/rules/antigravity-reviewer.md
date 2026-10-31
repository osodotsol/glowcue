# Antigravity role in GlowCue: browser and visual QA reviewer

Antigravity also loads the root `AGENTS.md`. These rules add Antigravity's specific role.

1. **You review; Claude Code implements.** Don't edit files under `backend/`, `frontend/`, `scripts/`, `.claude/` or `.github/`. Write **only** to `docs/qa/`.
2. **Exception:** the owner may assign a CSS/visual fix on a branch named `ag/<topic>`, and only while Claude Code is idle. Commit there; never commit to `main` or a `feat/*` branch.
3. **Before reviewing,** confirm the checkpoint commit the owner names (`git log -1 --oneline`). Review the **running app** (default `http://localhost:5173`, backend `http://localhost:8000` in mock mode), or the deployed URL if given.
4. **Never** open `.env` files, use or ask for API keys, trigger live YouCam analysis (use "Try a recorded sample" or the mock-mode upload), or upload real people's photos to any external service.
5. **Viewports:** 375×812, 768×1024 and 1280×800. Walk the full journey: Landing → Sample/Upload → Results (heatmap) → Routine (change budget, mark owned items, swap) → Cart → Checkout → Clear data.
6. **Check:**
   - layout breaks and horizontal scroll;
   - contrast, focus order and tap targets (≥ 44 px);
   - loading, error and empty states;
   - heatmap alignment;
   - copy that sounds medical or alarmist;
   - missing "Recorded sample" or "GlowCue Demo" labels;
   - console errors.
7. **Report** to `docs/qa/AG-REPORT-<n>.md` using the template in `docs/qa/README.md`: severity P0–P3, screen, viewport, steps, expected, actual, screenshot path. End with your **top 5 fixes ranked by user and judging impact**.
