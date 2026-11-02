# Phase 0: Foundation and engineering system

**Objective:** a working, validated engineering environment and runnable skeletons, before any product features are built.
**Prompt:** [01-project-foundation](../prompts/01-project-foundation.md) · **Branch:** `chore/project-foundation` · **Depends on:** nothing

## Tasks
1. Audit the workspace (read-only).
2. Set up git with a safe `.gitignore`, `.githooks/pre-commit` and `core.hooksPath`.
3. Instruction system: `AGENTS.md`, `CLAUDE.md`, `.claude/rules/*`, `.agents/rules/*`.
4. Skills (12), agents (7), `.claude/settings.json` with permissions and hooks, hook scripts plus tests.
5. Knowledge base in `docs/` (this structure), ADRs, prompts, PROJECT_STATUS.
6. Backend skeleton: FastAPI `/api/health`, settings, pytest, ruff. Frontend skeleton: Vite React TS, Tailwind v4, ESLint.
7. `.github/`: CI, PR template, issue templates, CONTRIBUTING.
8. Validation (`scripts/validate_project.py`), then commit and, if a remote and auth exist, PR #1.

## Acceptance checks
- [ ] `python scripts/validate_project.py` exits 0.
- [ ] `pytest scripts/tests backend/tests` green; ruff clean.
- [ ] `npm run lint && npm run typecheck && npm run build` green.
- [ ] `git check-ignore backend/.env` matches. No secrets in tracked files (`check_secrets.py --all`).
- [ ] Hooks verified by tests **and** a live smoke test inside Claude Code.
- [ ] Owner can see the skills in the `/` menu after restarting Claude Code.

## Outputs
Committed foundation on `chore/project-foundation`, plus PR #1 (or locally prepared PR instructions).

## Owner actions
Rotate the YouCam key and paste the new one into `backend/.env`. Install `gh` and log in. Create the GitHub repo. Fix the git email (see PROJECT_STATUS).
