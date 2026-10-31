---
paths:
  - "docs/**"
  - "README.md"
  - "AGENTS.md"
  - "CLAUDE.md"
---
# Documentation rules

- **Status truth:** `docs/PROJECT_STATUS.md` is the live record. Update it at the end of every task with the current phase, completed items, real test results, blockers, decisions awaiting the owner, PR links and the next action, timestamped in WAT.
- **Planned ≠ implemented:** design docs describe the plan. Mark anything built with "Implemented in PR #n", or record it in PROJECT_STATUS. Never describe a planned feature as working.
- **Decisions:** any change to the stack, API approach, data model or scope gets an ADR in `docs/decisions/` (Context, Options, Decision, Reason, Consequences) and a line in PROJECT_STATUS.
- **Contracts move together:** an endpoint change updates `docs/API_CONTRACTS.md` and `docs/DATA_MODEL.md` in the same commit.
- **Evidence tags:** keep the [V]/[A]/[R]/[U] tags accurate. Upgrade [U] to [V] only with a recorded source or probe result.
- **No duplication:** link to the owning doc instead of copying text. The docs index is `docs/README.md`.
- **Links:** use relative links. `python scripts/validate_project.py` checks them, so run it after doc edits.
- **No secrets or personal data** in docs, including screenshots that show keys, emails or a face without consent.
