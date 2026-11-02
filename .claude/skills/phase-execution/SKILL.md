---
name: phase-execution
description: Executes one authorised GlowCue implementation task end to end. Loads its prompt file from docs/prompts/, plans the change, implements it in small tested steps on the right feature branch, verifies the acceptance criteria and writes a completion report. Use when the owner authorises a specific task or prompt (e.g. "run prompt 06", "do the recommendation engine").
argument-hint: "<prompt-file-or-task-id>"
---

# Phase Execution

## Prerequisites
- The owner has authorised this task (in this conversation, or recorded in PROJECT_STATUS).
- Dependencies listed in the prompt file are done.
- `git status` is clean, or only contains this task's work.

## Inputs
`$ARGUMENTS` is a prompt file such as `docs/prompts/06-recommendation-engine.md` or its number.

## Procedure
1. **Load context:** the prompt file, the docs it cites, and the matching `docs/implementation/PHASE_*.md` gate. Path-scoped rules load automatically when you open files.
2. **Branch:** switch to the prompt's branch (create it from up-to-date `main` if missing): `git switch -c <branch>` or `git switch <branch>`. Never commit on `main`.
3. **Plan (short, shown to the owner):** files to create or modify, the tests to write first, risks, and anything [U] that needs the owner.
4. **Implement incrementally.** For each unit, write the test, implement, run the narrow test, and commit at a meaningful checkpoint (`feat: …`). Use the domain skill for detail: `/backend-engineering`, `/frontend-engineering`, `/youcam-integration` or `/recommendation-engine`.
5. **Stay in scope.** List anything else you notice under "Open issues" instead of fixing it.
6. **Verify:** run `/test-and-verify` for the touched areas. Every acceptance criterion gets a pass/fail with evidence.
7. **Document:** update the docs the prompt names, the contracts if any endpoint changed, and an ADR if a decision changed.
8. **Close:** run `/project-orchestrator close <task-id>`. If the milestone in the phase gate is complete, propose `/pr-workflow`.

## Completion report (always, in this shape)
```
Task: <id + title>       Branch: <branch>     Commits: <shas>
Files changed: <list>
Commands & results: <command → real output summary>
Acceptance criteria: <each → PASS/FAIL + evidence>
Open issues / follow-ups: <list>
Owner actions needed: <list or "none">
Next recommended step: <one line>
```

## Completion criteria
All acceptance criteria PASS with evidence, docs updated, status closed, working tree clean.
