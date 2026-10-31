# ADR-004: Engineering operating system (Claude Code + Antigravity + GitHub)

- **Status:** Accepted, 31 Oct 2026

## Context
Development is mostly AI-driven under a tight deadline. We need repeatable procedures, independent review, deterministic safety and a single source of truth that two different agent tools can follow without conflicting edits.

## Decision
- **Instructions:**
  - Shared conventions live in `AGENTS.md`, which Antigravity reads natively and Claude imports through `CLAUDE.md`.
  - Claude-only material goes in `CLAUDE.md`.
  - Topic rules go in `.claude/rules/`, path-scoped so backend and frontend rules load only when relevant.
  - Antigravity's role is defined in `.agents/rules/` (its documented location).
  - No directory-level `CLAUDE.md` files: the path-scoped rules cover the same need without duplication.
- **Procedures:** 12 Skills in `.claude/skills/*/SKILL.md`. Deployment and submission are manual-only (`disable-model-invocation`) because they act on external services.
- **Independent review:** 7 subagents in `.claude/agents/`, all without Edit/Write, so reviews stay independent and can't cause conflicting edits. Researcher and reviewers run on Sonnet to conserve Pro-plan usage.
- **Deterministic enforcement over prose:** permission rules plus PreToolUse hooks (command and edit guards), a git pre-commit secret scan and CI. Guard behaviour is unit-tested.
- **Git:** `main` receives only reviewed PRs. Claude may push feature branches and open PRs (with an ask prompt), but never merges.
- **Status:** `docs/PROJECT_STATUS.md` is the cross-session memory of the project.

## Consequences
- A small amount of setup overhead (about 1 hour) in exchange for safer, faster later phases.
- Hooks assume `python` on PATH (true on the owner's machine). CI runs the same scripts.
- Remote PRs need the GitHub CLI and a remote repo, which are pending owner actions.
