# 17: Security and privacy review

**Branch:** `fix/security-<topic>` (only if fixes are needed) · **Phase:** 5 · **Skill:** `/security-review` · **Reviewer:** `security-reviewer` · **Depends on:** 15

## Objective
Verify GlowCue meets every control in `docs/SECURITY_PRIVACY.md` before deployment, and fix any High finding.

## Context
`docs/SECURITY_PRIVACY.md`, `.claude/rules/security.md`, `.claude/skills/security-review/SKILL.md`.

## Instructions
1. Run the `/security-review` procedure in full (secrets in tree and history, bundle grep after `npm run build`, `.env` ignore check).
2. Delegate an independent pass to `security-reviewer` with the photo-lifecycle and abuse-control checklists.
3. Verify the application controls (SECURITY_PRIVACY §5) one by one, each with test evidence or a code reference.
4. Fix High and Medium findings on `fix/security-*` branches, test-first where possible.
5. Write `docs/qa/SECURITY-REVIEW-<date>.md` and update SECURITY_PRIVACY if a control changed.
6. **Remind the owner** to confirm the exposed key was rotated (you can't verify this yourself).

## Expected files
`docs/qa/SECURITY-REVIEW-<date>.md`, plus fixes and tests as needed.

## Constraints
Never read `.env`. Report secret locations, never values.

## Acceptance criteria
Zero High findings. Every SECURITY_PRIVACY §5 control has evidence. Owner confirms key rotation.

## Required tests
Tests for each fixed finding. Full `/test-and-verify all`.

## Definition of completion
Report committed. PROJECT_STATUS notes the review result.
