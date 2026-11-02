# Security & Privacy Guide

Policy rules for agents: `.claude/rules/security.md`. This document explains the **controls** and the **permission model** for the owner and reviewers.

## 1. Threat model (short)
| Asset | Threat | Primary control |
|---|---|---|
| YouCam API key | Committed to Git, shipped in the frontend, printed in logs or chat, quota theft | Server-side env only. Permission deny rules, hooks, pre-commit and CI secret scans. Key rotation. |
| User selfies (biometric-like personal data) | Persisted, logged, leaked through storage or the repo | In-memory processing, EXIF strip, consent gate, TTL results, YouCam task deletion, photo commit guard |
| YouCam units (1,000) | Abuse of the public live endpoint, runaway dev calls, accidental calls from scripts or tests | Owner permission prompt for live calls (§4.2), backend choke point and `.env`-authoritative mode (§4.4), network-isolated tests, per-IP and global caps, credit floor, kill switch, sample mode |
| Trust / claims | Medical-sounding advice | Cosmetic copy rules, banned-word test, disclaimers |

## 2. Credential handling
- **Location:** `backend/.env` (local, gitignored) and Render environment variables (production). Nowhere else.
- **Access:** only `backend/app/config.py` reads `YOUCAM_API_KEY`.
- **Rotation:** the first key was exposed in a chat transcript on 31 Oct 2026, so it is treated as compromised. **Owner action:** YouCam console → API Keys → create a new key → delete the old one → paste the new key into `backend/.env` yourself. Units belong to the account, not the key.
- **If a key ever reaches Git:** rotate it immediately. Removing it from history needs an owner-approved force-push and is not enough on its own.
- The console's "secret key" (`MIGfMA0…`) is an RSA *public* key for the legacy v1 flow. GlowCue doesn't use it. The scanners still flag it so it never gets committed by accident.

## 3. Photo lifecycle
Client (validate type/size, resize ≤ 2048 px, canvas re-encode strips EXIF) → HTTPS → backend (consent check → size, MIME and magic-byte check → Pillow re-encode, in memory) → YouCam presigned PUT → task → results (scores + masks) → in-memory TTL store (30 min) → YouCam task delete (if verified, see YOUCAM_API §6.8). The image bytes are discarded after the PUT. Nothing is written to disk. YouCam auto-deletes all files after 30 days [V].

## 4. Guardrails: what is protected, and what is not

The guardrails are **layers that make unintended spending and leaks unlikely, and make deliberate ones visible.** They are *not* a sandbox, and no document should claim they stop every possible execution path. Section 4.3 lists the known gaps; section 4.4 lists the backend rules that actually close them.

### 4.1 Layers
| Layer | Mechanism | What it enforces | Where |
|---|---|---|---|
| 1 | Claude Code **permission rules** (native, no Python needed) | **Deny** read/edit of env files (`.env`, named `.env.*` variants, any `*.env`; the `.example` files stay readable), edits to `settings.local.json`, `gh pr merge`, `gh repo delete/edit`, force-push. **Ask** before push, PR create/edit, `gh api`, installs, any Bash/PowerShell command containing the YouCam host or `YOUCAM_MODE=live`, and edits to hooks, `settings.json`, git hooks, the scanner, guard tests, the validator, CI workflows and `.gitignore`. Bypass mode disabled. | `.claude/settings.json` |
| 2 | **PreToolUse hook** `guard_bash.py` (Bash, PowerShell, Monitor) | **Deny:** reading/copying env files (also through `bash -c`, `timeout`, `xargs` and similar), env dumps, `$YOUCAM_API_KEY` expansion, staging `.env`, `--no-verify`, force-push, remote-branch delete, hard resets, PR merge, repo edits, catastrophic `rm -rf`, secret literals. **Ask the owner** (see 4.2) for anything that could reach YouCam or switch to live mode, and for anything that could modify a guardrail file. | `.claude/hooks/guard_bash.py` |
| 3 | **PreToolUse hook** `guard_edits.py` (Write, Edit, MultiEdit, NotebookEdit) | **Deny:** any env-style file, secret-looking content. **Ask:** edits to guardrail files. | `.claude/hooks/guard_edits.py` |
| 4 | **Fail-closed wiring** | Hooks are configured with `onFailure: "block"` and `\|\| exit 2`, so a crash, timeout or missing Python **blocks** the action. Malformed input, unexpected input shapes, internal errors and a missing pattern module all produce an owner prompt (or a deny for visible secrets), never a silent allow. | `.claude/settings.json`, hook code |
| 5 | **Git pre-commit hook** | `check_secrets.py --staged`: secret patterns, forbidden files, photos outside approved folders | `.githooks/pre-commit` (`git config core.hooksPath .githooks`) |
| 6 | **CI** | Validator (including the fail-closed wiring), secret scans of files and history, guard tests, backend and frontend checks | `.github/workflows/ci.yml` |
| 7 | **Test isolation** | Backend tests never read `backend/.env` or any YouCam variable, and **any outbound network access fails the test** (httpx transports, sockets, DNS). `httpx.MockTransport` still works. | `backend/tests/conftest.py`, `test_network_isolation.py` |
| 8 | **GitHub** | The owner reviews and merges every PR. **Branch protection on `main` is not yet enabled**; configure it right after PR #1 merges (require a PR and the 3 CI checks, block force-push). GitHub's push protection only knows provider formats, not YouCam keys, so layers 2-7 are the real backstop. | GitHub settings |

### 4.2 How the live-call gate works
A hook returns `permissionDecision: "ask"`; Claude Code then shows **you** a permission prompt (in auto mode the classifier does not decide hook "ask" decisions, per the hooks documentation). The agent cannot answer it. There is **no token or environment variable** that skips it, and the old `GLOWCUE_LIVE_APPROVED` mechanism has been removed (tests assert both).

The classification is **default-ask**: a command is treated as live-capable when a YouCam marker (API host, `probe_youcam`, `youcam_client`, `youcam_base_url`, `youcam_api_key`) or a mode switch (`YOUCAM_MODE`, `LIVE_ANALYSIS_ENABLED`, `--env-file`, `dotenv`, sourcing an env file) appears anywhere in the command, unless **every executing part** is provably inert (git, echo, cat, grep, a known read-only tool run, a pytest run, the repo's own validator and scanner). This is what covers wrappers (`bash -c`, `sh -c`, `powershell -Command`, `cmd /c`, `timeout`, `nice`, `command`, `xargs`, `uv run`, subshells and pipes) without listing each one. The guard also reads the files a command runs (Python scripts and their local imports, Node scripts, curl config files, `python -m` modules, patch files) and asks if they contain YouCam code or target guardrail files.

Prose that merely *mentions* a marker or path (commit messages, PR bodies, `grep`, `cat`, `git diff`) does not prompt.

**Always choose the one-time "Yes" on these prompts.** "Yes, and don't ask again" can save a permanent allow rule in `.claude/settings.local.json` for the matching command. Agent edits to that file are denied, but your own click is not, and whether a saved allow rule silences a *hook* "ask" is not documented, so treat it as unsafe.

### 4.3 Known limitations (not covered)
1. **Obfuscated or constructed commands.** Text inspection cannot see a host assembled from fragments, an encoded payload, or an alias or function defined elsewhere. These are recorded as strict expected-failure tests (`test_KNOWN_LIMIT_*`), so any change in that behaviour is noticed.
2. **Config-driven calls.** A script that gets its target from configuration at run time (for example, a helper that reads the base URL from the environment) is only caught if the file or its local imports contain a marker. **This gap is closed in the backend, not the hook: see 4.4.**
3. **Pytest runs are exempt from the prompt** (they are routine and must mock all HTTP). Layer 7 blocks real network access in tests, but a test that deliberately removes the isolation fixture would not be caught by the hooks.
4. **Not a sandbox.** Only Bash, PowerShell and Monitor are matched today. If a new tool that runs commands appears (for example an MCP server), extend the matcher.
5. **You are the final control.** The hooks assume you read each prompt. The units ledger in `PROJECT_STATUS.md` records every live run, so an unexpected balance drop is visible; you can also compare it with the console's usage history.
6. **Not every file is a guardrail.** `ruff.toml` (formatter settings), `CLAUDE.md` and the rules are intentionally not protected.
7. **Prompt delivery is verified manually.** The unit tests prove the hooks return `ask`; that Claude Code then shows you a prompt was checked by hand once (see `PROJECT_STATUS.md`).

### 4.4 Required application safeguards (Phase 1/2 backend; findings M1 and M2)
Command inspection can never be the *decisive* control. These requirements make the **application itself** refuse to spend units unless the owner has set it up. They are acceptance criteria for [prompt 02](prompts/02-backend-architecture.md) and [prompt 03](prompts/03-youcam-api-integration.md):

| # | Requirement | Why |
|---|---|---|
| B1 | **`backend/.env` is the authority for live capability.** Configure settings sources so that values in `backend/.env` take priority over process environment variables for `YOUCAM_MODE` and `LIVE_ANALYSIS_ENABLED` (production has no `.env` file, so Render's variables apply there). | A command can set an environment variable, but only the owner can edit `backend/.env` (agent edits are denied). |
| B2 | **One choke point.** All YouCam traffic goes through a single function (for example `YouCamClient._send`) that first requires `youcam_mode == "live"` **and** `live_analysis_enabled` **and** a non-empty key **and** the daily caps **and** the credit floor. No other module may create an HTTP client for YouCam. | A script, `python -c` snippet or import cannot reach YouCam without passing the same checks. |
| B3 | **Mock mode never constructs a real transport.** In mock mode the client is built with a mock transport or raises on any send. | Accidental calls in mock mode fail loudly. |
| B4 | **Startup log (no secrets):** the effective mode, `live_analysis_enabled` and whether a key is present. | Lets the owner see at a glance what a running server will do. |
| B5 | **Tests for B1-B3:** a `.env` value wins over a conflicting environment variable; a live-mode call without the second flag is refused; the choke point is the only module that mentions the YouCam base URL (a test checks the source); the client in mock mode raises on `send`. | Keeps the controls from regressing. |
| B6 | **Live endpoints stay off by default** (`LIVE_ANALYSIS_ENABLED=false`) and the sample endpoint never calls YouCam. | Visitors cannot trigger spending unless the owner switches it on. |

**Implementation status (Phase A, 1 Nov 2026, tested offline):**
- **B1:** `Settings.settings_customise_sources` orders init, `backend/.env`, then environment (`backend/app/config.py`). The YouCam host is no longer configurable.
- **B2:** `YouCamClient._send` in `backend/app/services/youcam_client.py` is the only route to YouCam. It refuses unless mode, kill switch and key line up. The credit floor is read (free call) before any upload; the daily caps are enforced in `services/limits.py` before the photo is accepted.
- **B3:** outside live mode the client is built with a transport that raises on any request, even if a transport is passed in.
- **B4:** a startup log line reports the mode, the kill switch and whether a key is present.
- **B5:** `backend/tests/test_live_safeguards.py`, including source scans: only `youcam_client.py` mentions the host or imports httpx.
- **B6:** `LIVE_ANALYSIS_ENABLED` defaults to false; `POST /api/analyses` answers `503 live_unavailable` until the owner enables it.
- **Also:** consent is checked before the photo is read; photos are read as a capped raw body (never spooled to disk), checked by signature, re-encoded into a fresh metadata-free JPEG in memory, and dropped after upload; the YouCam task is deleted after success or a task error; the `httpx`/`httpcore` loggers are held at WARNING so request URLs (presigned upload URLs, task ids) are never logged.

### 4.5 Why mock mode is the default
1. **Units are scarce and irreplaceable:** 1,000 units is roughly 71 analyses, and judging runs to 21 Nov. Every accidental call lowers what judges can try.
2. **A safe default makes mistakes cheap:** a forgotten setting, a stray test or a copied command costs nothing in mock mode.
3. **It matches the organisers' guidance:** a public build that replays a recorded real response satisfies the testing requirement, so live calls are optional extras rather than the baseline.
4. **Live mode needs three things to line up** (owner-edited `.env` mode, the enable flag, and a key), plus an owner permission prompt for any command that touches it.

**Permission model in plain words:** Claude can read and edit project files, run tests and builds, and commit on feature branches without asking. It must ask before anything leaves your machine (push, PR, installs) and before anything that could spend YouCam units or change the guardrails. It cannot read or write your env files, merge PRs, force-push or change repository settings.

## 5. Application controls (to implement; status in PROJECT_STATUS)
Consent required · 10 MB limit · JPEG/PNG only (magic bytes) · min 480 px short side · per-IP 5 per day · global 25 per day · credit floor 100 · `LIVE_ANALYSIS_ENABLED` kill switch · CORS restricted to `FRONTEND_ORIGIN` · server-side cart pricing · no SSRF · redacted logging · **plus B1-B6 above**.

## 6. Incident response
1. **Key exposed:** rotate in the console, update Render and `backend/.env`, run `check_secrets.py --history`, note it in PROJECT_STATUS.
2. **Quota draining:** set `LIVE_ANALYSIS_ENABLED=false` on Render (sample mode keeps working), check the logs for the source, then lower the caps.
3. **Photo committed:** don't push. If already pushed, make the repo private (owner), remove the file with an owner-approved history rewrite, and inform the person.
