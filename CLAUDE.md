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

## Guardrails already enforced (see `docs/SECURITY_PRIVACY.md`)
- Permission rules deny reading or editing `.env` files, force-push, `gh pr merge` and repo edits. Pushes and PR creation ask first.
- Hooks block the following:
  - secret-looking content in edits;
  - commands that read `.env`, dump the environment, skip git hooks or run destructive resets;
  - **live YouCam calls unless the command carries `GLOWCUE_LIVE_APPROVED=1`**. Add that only after the owner approves *that specific* call.
- Python files are auto-formatted with ruff after edits.
- The git pre-commit hook (`.githooks/pre-commit`) and CI rerun the secret scan.

If a guard blocks you, don't hunt for a workaround. Explain why it was blocked and ask the owner.

## Working style
- Make small, testable increments, one prompt file per task. Don't refactor code outside the task.
- The owner is strong in Python and newer to full-stack work, so explain non-obvious decisions in plain language in completion reports.
- Every task ends with a completion report: files changed, commands run with real results, acceptance criteria pass/fail, open issues and the next step.
