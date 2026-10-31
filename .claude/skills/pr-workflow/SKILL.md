---
name: pr-workflow
description: Prepares, reviews and opens a GitHub pull request for a completed GlowCue milestone. Covers git status and diff review, tests, lint, secret scan, an independent pr-reviewer subagent pass, fixes, a Conventional Commit, push, and gh pr create with the repo template. Also tracks review feedback and CI results. Never merges. Use when a milestone in docs/implementation/ is complete or the owner asks to open a PR.
argument-hint: "[base branch, default main]"
---

# PR Workflow

## Prerequisites
- You're on a feature branch (`chore/`, `docs/`, `feat/`, `fix/`, `test/`), never `main`.
- Remote PRs need the GitHub CLI (`gh --version`), an authenticated session (`gh auth status`) and a verified remote (`git remote -v`) owned by the user. If any is missing, prepare everything locally and give the owner the exact commands (see Fallback).

## Procedure
1. **Inspect:** `git status`, `git log --oneline main..HEAD`, `git diff --stat main...HEAD`, then read the full diff. Look for stray files (logs, `.env`, photos, `dist/`, `node_modules/`) and debug code.
2. **Verify:** run `/test-and-verify all` and `python scripts/security/check_secrets.py --all`. Everything must be green.
3. **Independent review:** delegate to the `pr-reviewer` subagent with the branch name, base, task ids and the acceptance criteria. If the diff touches uploads, config, secrets or CI, also delegate to `security-reviewer`.
4. **Resolve** every Blocker or High finding with new commits, never by force-pushing. Re-run step 2. Record anything deferred under "Outstanding issues".
5. **Sync:** `git fetch origin && git merge origin/main` if the base moved, then re-test. Never rebase a pushed branch without owner approval.
6. **Push.** The owner approves when prompted: `git push -u origin <branch>`.
7. **Open the PR.** Fill `.github/PULL_REQUEST_TEMPLATE.md` completely: purpose, summary, related phase, acceptance criteria with evidence, tests with real output, screenshots for UI, security and docs checklists, outstanding issues. Then run `gh pr create --base main --head <branch> --title "<type>: <summary>" --body-file <tmp-body.md>`.
8. **Track:** `gh pr checks <n> --watch` for CI and `gh pr view <n> --comments` for feedback. Fix on the same branch.
9. **Record:** add the PR URL to `docs/PROJECT_STATUS.md`. **Stop.** The owner reviews and merges.

## Fallback (no gh, auth or remote)
Report "PR prepared locally; not opened", with the branch name, the body file path, and the exact commands:
```bash
winget install --id GitHub.cli        # once
gh auth login                         # once, choose GitHub.com + HTTPS + browser
git remote add origin https://github.com/<you>/glowcue.git   # once
git push -u origin main && git push -u origin <branch>
gh pr create --base main --head <branch> --title "..." --body-file <file>
```

## Commit message convention
`<type>(<scope>): <imperative summary>`, then a body explaining why, then the trailer `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`.

## Never
Merge, force-push, delete remote branches, change visibility, bypass failed CI, or push secrets or personal photos.
