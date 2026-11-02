---
name: security-review
description: GlowCue security and privacy audit. Covers secret scanning (working tree and git history), .gitignore and .env protection, API-key exposure (including the frontend bundle), photo handling (memory-only, EXIF, consent, TTL, deletion), input validation, unsafe logging, CORS, rate and quota limits, and dependency vulnerabilities. Use before any push or PR that touches backend services, config, uploads or CI; before deployment; and before final submission.
---

# Security and Privacy Review

Policy: `.claude/rules/security.md`. Guide: `docs/SECURITY_PRIVACY.md`.

## Procedure
1. **Secrets:**
   - `python scripts/security/check_secrets.py --all` (tree)
   - `python scripts/security/check_secrets.py --history` (all commits)
   - `git check-ignore -v backend/.env` must print a match
   - `git ls-files | grep -iE '(^|/)\.env($|\.)' | grep -v example` must print nothing
2. **Frontend bundle:** after `npm run build`, run `grep -rEn "sk-[A-Za-z0-9_-]{20,}|YOUCAM" frontend/dist`. It must print nothing.
3. **Photo handling.** Delegate to the `security-reviewer` subagent with this checklist:
   - uploads are read into memory only (no `open(..., "wb")`, `tempfile`, or `UploadFile.file` saved to disk);
   - Pillow re-encode strips metadata;
   - consent is checked before processing;
   - the results store has a TTL;
   - no image or base64 in logs;
   - the YouCam task is deleted after retrieval (if verified).
4. **Input validation:** size limit, MIME and magic-byte check, dimension check, Pydantic models on every body, no user-supplied URLs fetched.
5. **Abuse and quota:** per-IP and global daily caps, credit floor, `LIVE_ANALYSIS_ENABLED` kill switch, 429 handling.
6. **CORS and headers:** CORS allows only `FRONTEND_ORIGIN`; no wildcard with credentials.
7. **Dependencies:**
   - `cd frontend && npm audit --omit=dev`
   - backend: `.venv/Scripts/python -m pip_audit -r requirements.txt` if pip-audit is installed. If not, list pinned versions and note the gap.
8. **Report** in `docs/qa/SECURITY-REVIEW-<date>.md`: finding, severity (High/Med/Low), evidence (file:line), fix, status. Update `docs/SECURITY_PRIVACY.md` if a control changed.

## Severity policy
Any High (a key exposed, a photo persisted, missing consent, no upload limit) blocks a PR, deploy or submission until fixed.

**If a key is found in history:** tell the owner to **rotate it in the YouCam console immediately**. History rewriting needs owner approval and isn't sufficient on its own.

## Completion criteria
Zero High findings. The report is committed. PROJECT_STATUS notes the review date and result.
