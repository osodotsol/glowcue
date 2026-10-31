# Security & Privacy Guide

Policy rules for agents: `.claude/rules/security.md`. This document explains the **controls** and the **permission model** for the owner and reviewers.

## 1. Threat model (short)
| Asset | Threat | Primary control |
|---|---|---|
| YouCam API key | Committed to Git, shipped in the frontend, printed in logs or chat, quota theft | Server-side env only. Permission deny rules, hooks, pre-commit and CI secret scans. Key rotation. |
| User selfies (biometric-like personal data) | Persisted, logged, leaked through storage or the repo | In-memory processing, EXIF strip, consent gate, TTL results, YouCam task deletion, photo commit guard |
| YouCam units (1,000) | Abuse of the public live endpoint, runaway dev calls | Per-IP and global daily caps, credit floor, kill switch, live-call approval token, sample mode |
| Trust / claims | Medical-sounding advice | Cosmetic copy rules, banned-word test, disclaimers |

## 2. Credential handling
- **Location:** `backend/.env` (local, gitignored, created empty) and Render environment variables (production). Nowhere else.
- **Access:** only `backend/app/config.py` reads `YOUCAM_API_KEY`.
- **Rotation:** the first key was exposed in a chat transcript on 31 Oct 2026, so it is treated as compromised. **Owner action:** YouCam console → API Keys → create a new key → delete the old one → paste the new key into `backend/.env` yourself. Units belong to the account, not the key.
- **If a key ever reaches Git:** rotate it immediately. Removing it from history needs an owner-approved force-push and is not enough on its own.
- The console's "secret key" (`MIGfMA0…`) is an RSA *public* key for the legacy v1 flow. GlowCue doesn't use it. The scanners still flag it so it never gets committed by accident.

## 3. Photo lifecycle
Client (validate type/size, resize ≤ 2048 px, canvas re-encode strips EXIF) → HTTPS → backend (consent check → size, MIME and magic-byte check → Pillow re-encode, in memory) → YouCam presigned PUT → task → results (scores + masks) → in-memory TTL store (30 min) → YouCam task delete (if verified, see YOUCAM_API §6.8). The image bytes are discarded after the PUT. Nothing is written to disk. YouCam auto-deletes all files after 30 days [V].

## 4. Guardrails: defence in depth
| Layer | Mechanism | What it enforces | Where |
|---|---|---|---|
| 1 | Claude Code **permission rules** | Deny read and edit of `.env*` (not examples), `gh pr merge`, `gh repo delete/edit`, force-push. **Ask** before push, PR create/edit/comment, `gh api`, package installs. Bypass mode disabled. | `.claude/settings.json` |
| 2 | **PreToolUse hook** `guard_bash.py` | Blocks reading or copying `.env`, env dumps, `$YOUCAM_API_KEY` expansion, `git add -f`, staging `.env`, `--no-verify`, force-push, remote branch delete, `reset --hard`/`clean -f`, PR merge, repo edits, catastrophic `rm -rf`, secret literals in commands, and **live YouCam traffic without `GLOWCUE_LIVE_APPROVED=1`** | `.claude/hooks/` |
| 3 | **PreToolUse hook** `guard_edits.py` | Blocks writing `.env` files and any edit whose new content contains a secret pattern | `.claude/hooks/` |
| 4 | **Git pre-commit hook** | `check_secrets.py --staged`: secret patterns, forbidden files (`.env`, keys, `private/`, raw fixtures), photos outside approved folders | `.githooks/pre-commit` (`git config core.hooksPath .githooks`) |
| 5 | **CI** | Secret scan of all tracked files, guard tests, lint, tests, build | `.github/workflows/ci.yml` |
| 6 | **GitHub** | Push protection for secrets (on by default for public repos). The owner reviews and merges every PR. | GitHub settings |

Every guard is covered by tests in `scripts/tests/test_security_guards.py`.

**Permission model in plain words:** Claude can read and edit project files, run tests and builds, and commit on feature branches without asking. It must **ask** before anything leaves your machine (push, PR, API calls to GitHub, installs). It **cannot** read your `.env`, merge PRs, force-push, or change repository settings, and the hooks stop it from spending YouCam units unless you approve a specific command.

## 5. Application controls (to implement; status in PROJECT_STATUS)
Consent required · 10 MB limit · JPEG/PNG only (magic bytes) · min 480 px short side · per-IP 5 per day · global 25 per day · credit floor 100 · `LIVE_ANALYSIS_ENABLED` kill switch · CORS restricted to `FRONTEND_ORIGIN` · server-side cart pricing · no SSRF · redacted logging.

## 6. Incident response
1. **Key exposed:** rotate in the console, update Render and `backend/.env`, run `check_secrets.py --history`, note it in PROJECT_STATUS.
2. **Quota draining:** set `LIVE_ANALYSIS_ENABLED=false` on Render (sample mode keeps working), check the logs for the source, then lower the caps.
3. **Photo committed:** don't push. If already pushed, make the repo private (owner), remove the file with an owner-approved history rewrite, and inform the person.
