# 19: GitHub pull request creation (every milestone)

**Branch:** the current feature branch · **Skill:** `/pr-workflow` · **Reviewers:** `pr-reviewer` (always), `security-reviewer` (if uploads, config, secrets or CI changed)

## Objective
Turn a completed milestone into a clean, reviewed, CI-green pull request against `main`, without ever merging it.

## Context
`.claude/skills/pr-workflow/SKILL.md`, `.github/PULL_REQUEST_TEMPLATE.md`, `.github/CONTRIBUTING.md`, the milestone's gate in `docs/implementation/`.

## Instructions
1. Confirm the gate's acceptance checks are met (PROJECT_STATUS evidence).
2. Inspect the diff vs `main`. Remove stray files. Run `/test-and-verify all` and the secret scan.
3. Run `pr-reviewer`, plus `security-reviewer` if relevant. Resolve Blockers and Highs with new commits.
4. Merge `origin/main` into the branch if it moved, then re-test.
5. Push (owner approves the prompt) and run `gh pr create` with a fully filled template body (real test output, screenshots for UI).
6. Watch CI (`gh pr checks --watch`). Fix failures on the branch.
7. Record the PR URL in PROJECT_STATUS. **Stop: the owner reviews and merges.**
8. If `gh`, auth or the remote is missing, follow the skill's Fallback and report "prepared locally".

## Expected files
None beyond the branch's own changes, plus the PROJECT_STATUS update.

## Constraints
Never merge, force-push, delete remote branches, change visibility or bypass CI.

## Acceptance criteria
PR open with CI green and a complete body, or exact local instructions are given.

## Required tests
The full matrix for the touched areas.

## Definition of completion
PR URL recorded, or fallback instructions delivered.
