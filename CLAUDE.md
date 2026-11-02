# GlowCue — Claude Code Instructions

@AGENTS.md

## Start of every session
1. Read `docs/PROJECT_STATUS.md` to see where work stopped, what's blocked and what's next.
2. Run the `/project-orchestrator` skill to confirm the next task. Don't start a phase the owner hasn't authorised.
3. Check `git status` and the current branch. Never work directly on `main`.

## Where instructions live (don't duplicate them here)
| Need | Location |
|---|---|
| Coding rules (auto-loaded per path) | `.claude/rules/` with general, security, backend, frontend, testing, api-integration and documentation files |
| How to do a type of task | `.claude/skills/<name>/SKILL.md`, invoked with `/name` |
| Independent reviews | `.claude/agents/`: api-researcher, software-architect, backend-reviewer, frontend-reviewer, qa-engineer, security-reviewer, pr-reviewer |
| What to build next | `docs/IMPLEMENTATION_ROADMAP.md`, `docs/implementation/PHASE_*.md`, `docs/prompts/*.md` |
| Why a decision was made | `docs/decisions/ADR-*.md` |

## Skills (invoke with `/name`)
`project-orchestrator` · `phase-execution` · `youcam-integration` · `backend-engineering` · `frontend-engineering` ·
`recommendation-engine` · `design-review` · `test-and-verify` · `security-review` · `pr-workflow` ·
`deployment-release`\* · `hackathon-submission`\*  (\* manual only: they affect external services)

## Using subagents
Use a reviewer agent when an **independent** view adds value: before a PR (`pr-reviewer`, plus `security-reviewer` when touching uploads, config or secrets), or after a large UI phase (`frontend-reviewer`). Don't spawn agents for routine work. Reviewers never edit files. The main session decides and integrates.

## Guardrails (best-effort layers, NOT a sandbox; full detail and known limits in `docs/SECURITY_PRIVACY.md`)
- **Deny:** permission rules and hooks refuse to read or write env files, dump the environment, skip git hooks, force-push, merge PRs, edit repo settings or run destructive resets, and refuse secret-looking content in edits and commands.
- **Ask (a real prompt only the owner can answer):**
  - any command that could reach YouCam or switch the backend to live mode: the API host, the probe script, `YOUCAM_MODE` and `LIVE_ANALYSIS_ENABLED`, `--env-file`, scripts or their imports containing YouCam client code, including when hidden behind `bash -c`, `timeout`, `xargs`, `uv run` and similar;
  - any command or edit that could change a guardrail file: `.claude/hooks`, `.claude/settings*.json`, `.githooks/`, `scripts/security/`, the guard tests, the validator, CI workflows or `.gitignore`.
- No token or variable bypasses a prompt. Ask in chat first, and never reshape a command to avoid one.
- **Fail closed:** a crashing or missing guard blocks the action; malformed input asks.
- **Not covered:** obfuscated or constructed commands, config-driven calls, and deliberate test tampering. The backend must therefore enforce live mode itself (`docs/SECURITY_PRIVACY.md` §4.4). Backend tests are network-isolated and never see the real key.
- Python files are auto-formatted with ruff after edits. The git pre-commit hook and CI rerun the secret scan.

If a guard blocks you, don't hunt for a workaround. Explain why it was blocked and ask the owner.

## Working style
- Make small, testable increments, one prompt file per task. Don't refactor code outside the task.
- The owner is strong in Python and newer to full-stack work, so explain non-obvious decisions in plain language in completion reports.
- Every task ends with a completion report: files changed, commands run with real results, acceptance criteria pass/fail, open issues and the next step.
