# General engineering rules (always loaded)

- **Scope discipline:** implement only the authorised task. If you notice other problems, list them in the completion report instead of fixing them silently.
- **Incremental change:** edit existing working code instead of rewriting it, and keep public interfaces stable (the API contracts in `docs/API_CONTRACTS.md` and the types in `frontend/src/lib/types.ts`).
- **One source of truth:** facts live in exactly one doc. Link to it rather than copying it.
- **Determinism:** the recommendation engine and normaliser are pure functions, with no randomness, time or network access.
- **Dependencies:** add a new package only when the standard library or an existing dependency can't reasonably do the job. Justify it in the completion report and pin it.
- **Naming:** Python uses `snake_case` modules and functions and `PascalCase` models. TypeScript uses `camelCase` for values and `PascalCase` for components and types. Concern keys use the normalised names (`dark_circles`, not `dark_circle_v2`).
- **Copy tone:** warm, plain English, cosmetic framing ("more visible", "helps the look of"). Never alarmist or medical.
- **Time awareness:** the hackathon deadline is fixed. Prefer the simplest design that meets the acceptance criteria. Features frozen in `docs/IMPLEMENTATION_ROADMAP.md` stay frozen.
- **Honesty:** never mark a task done, a test passing or a feature working without command output showing it.
