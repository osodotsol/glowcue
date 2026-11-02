# 01: Project foundation

**Branch:** `chore/project-foundation` · **Phase:** 0 · **Status:** executed 31 Oct 2026. Kept for reproducibility and for re-running validation.

## Objective
Set up the engineering operating system (instructions, rules, skills, agents, hooks, settings, docs, CI, PR templates) and runnable backend and frontend skeletons, with no product features.

## Context
`docs/implementation/PHASE_0_FOUNDATION.md`, `docs/decisions/ADR-001…004`, `docs/ARCHITECTURE.md` §7.6, `docs/SECURITY_PRIVACY.md`.

## Instructions
1. Audit read-only first: the directory, git state, toolchain versions, `gh`, and any existing `.claude/` config.
2. Write `.gitignore` before anything else. Create an empty `backend/.env` (`YOUCAM_API_KEY=`) and `backend/.env.example`. Verify `git check-ignore backend/.env`.
3. Create the instruction system, skills, agents, settings and hooks, plus `scripts/` (validator, secret scanner, guard tests) and `.githooks/pre-commit`.
4. Backend skeleton: `app/main.py` (`/api/health`), `app/config.py` (Settings, mock default), `tests/`, `pyproject.toml` (ruff + pytest), pinned `requirements*.txt`, `.python-version`.
5. Frontend skeleton: Vite + React + TS strict + Tailwind v4 + ESLint flat config. Scripts `dev`, `build`, `lint`, `typecheck`, `preview`. Add `frontend/.env.example`.
6. `.github/`: `workflows/ci.yml` (only commands that exist), PR template, issue templates, CONTRIBUTING.
7. Validate everything, commit on the branch, and open PR #1 if `gh`, auth and a remote exist. Otherwise prepare it locally.

## Expected files
`AGENTS.md`, `CLAUDE.md`, `.claude/**`, `.agents/rules/**`, `.githooks/pre-commit`, `.github/**`, `docs/**`, `scripts/**`, `backend/{app,tests}/**`, `backend/{pyproject.toml,requirements.txt,requirements-dev.txt,.env.example,.python-version}`, `frontend/**` (excluding `node_modules`), `README.md`, `LICENSE`, `.editorconfig`, `.gitattributes`.

## Constraints
No product features. No live API calls. Never use or reproduce any previously shared key. Don't merge.

## Acceptance criteria
Every check in PHASE_0_FOUNDATION passes.

## Required tests
`scripts/tests/test_security_guards.py`, `backend/tests/test_health.py`, `backend/tests/test_config.py`, plus frontend lint, typecheck and build.

## Definition of completion
Foundation committed, validation output recorded in PROJECT_STATUS, PR opened or exact remote steps given.
