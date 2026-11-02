---
name: project-orchestrator
description: Session-start and "what's next?" coordinator for GlowCue. Reads docs/PROJECT_STATUS.md and the roadmap, checks the real repo state, picks the next valid task and its prompt file, and keeps the status record truthful. Use at the start of every session, when the owner asks what to do next or where we are, and after finishing any task.
when_to_use: "Trigger phrases: what's next, where are we, status, continue, resume. Also at the start of a session and at the end of a task."
argument-hint: "[status|next|close <task-id>]"
---

# Project Orchestrator

Coordinates the GlowCue lifecycle. It **decides and records**. It doesn't implement: implementation goes through `/phase-execution`.

## Prerequisites
- Repo checked out. `docs/PROJECT_STATUS.md` and `docs/IMPLEMENTATION_ROADMAP.md` exist.

## Inputs
- `$ARGUMENTS`: `status` (default), `next`, or `close <task-id>` after a task finishes.

## Procedure
1. **Read state:** `docs/PROJECT_STATUS.md`, the phase table in `docs/IMPLEMENTATION_ROADMAP.md` (§10 and the timeline in §18), and `docs/implementation/README.md`.
2. **Check reality.** Run these, without assuming anything:
   - `git status --short` and `git branch --show-current`
   - `git log --oneline -5`
   - `python scripts/validate_project.py`
3. **Reconcile.** If the status file claims something reality contradicts (e.g. "tests green" but they fail, or a branch is missing), flag it at the top of the report and correct the status file.
4. **Time check.** Compute the hours left to the internal target (**Mon 2 Nov 2026, 14:00 WAT**) and the hard deadline (17:45 WAT). Compare against the roadmap timeline. If behind, propose items from the cut list in `docs/IMPLEMENTATION_ROADMAP.md` §18. Respect the feature freeze (Sun 1 Nov, 21:00 WAT).
5. **Select the next task.** Take the first incomplete task whose dependencies are done and whose blockers are cleared. Pending owner decisions and owner actions (key rotation, GitHub repo, selfies) are blockers. Name the matching `docs/prompts/NN-*.md` file and the branch to use.
6. **Present** a short report:
   - **Now:** phase, branch, last commit.
   - **Health:** validator, tests and scan results.
   - **Next task:** id, prompt file, estimate, acceptance criteria summary.
   - **Owner actions needed:** exact steps.
   - **Risks / time:** behind or ahead of plan.
7. **Wait for authorisation** unless the owner has already authorised that phase in this conversation.
8. **On `close <task-id>`:** update `docs/PROJECT_STATUS.md` with:
   - task → done;
   - real test output counts;
   - the PR link;
   - new blockers or decisions;
   - the next recommended action;
   - a timestamp in WAT.

   Add a row to the Change log section.

## Quality checks
- Every claim in the report is backed by a command you ran in this session.
- Exactly one recommended next task, and it isn't blocked.

## Output
The status report (step 6). After `close`, the updated `docs/PROJECT_STATUS.md`.

## Completion criteria
The owner knows what's done, what's next, what they must do, and how much time remains.
