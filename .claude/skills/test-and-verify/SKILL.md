---
name: test-and-verify
description: Runs the right GlowCue verification for a change and reports real results. Covers unit and API tests (pytest), guard tests, lint and format (ruff, ESLint), typecheck and build, the mock-mode end-to-end smoke test, failure scenarios, acceptance-criteria checks and regression checks. Use before closing any task, before a PR, after merging main into a branch, or whenever the owner asks "does it work?".
argument-hint: "[backend|frontend|e2e|all] (default: what changed)"
---

# Test and Verify

Plan: `docs/TEST_PLAN.md`. Rules: `.claude/rules/testing.md`.

## Prerequisites
`backend/.venv` and `frontend/node_modules` are installed. Mock mode is on (the default).

## Procedure
1. **Scope:** use `git diff --name-only main...HEAD` to choose suites. Anything under `backend/` gets backend checks, `frontend/` gets frontend checks, and `scripts/`, `.claude/` or `.githooks/` get repo checks. If nothing is given, use what changed. Use `all` before a PR.
2. **Run** each command and capture the summary line:

| Area | Command |
|---|---|
| Repo | `python scripts/validate_project.py` · `python scripts/security/check_secrets.py --all` · `backend/.venv/Scripts/python -m pytest scripts/tests -q` |
| Backend | `cd backend && .venv/Scripts/python -m ruff check . && .venv/Scripts/python -m ruff format --check . && .venv/Scripts/python -m pytest -q` |
| Frontend | `cd frontend && npm run lint && npm run typecheck && npm run build` (+ `npm run test` once Vitest exists) |
| E2E | `cd frontend && npx playwright test` (once `e2e/` exists; mock mode) |

3. **Failure scenarios:** when upload, analysis or limits code changed, walk through the matching rows of `docs/TEST_PLAN.md`, using automated tests where they exist and manual checks otherwise.
4. **Acceptance criteria:** for each criterion in the task's prompt file, state PASS or FAIL with evidence (a test name, command output, or a screenshot path).
5. **Regression:** if anything that passed before now fails, stop and report it. Don't paper over it by changing the test without a stated reason.
6. **Record:** paste the summary lines into the completion report and into `docs/PROJECT_STATUS.md` → "Latest test results".

## Quality checks
- Numbers come from this session's output, never from memory.
- Never commit anything that's red. If a test is flaky, report it. Don't delete it.

## Output
A verification table with area, command, result and duration, plus acceptance-criteria verdicts.
