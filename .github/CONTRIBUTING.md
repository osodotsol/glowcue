# Contributing to GlowCue

## Workflow
1. Branch from `main`: `feat/<topic>`, `fix/<topic>`, `chore/<topic>`, `docs/<topic>`, `test/<topic>`. Antigravity visual fixes use `ag/<topic>`.
2. Make small, tested commits using [Conventional Commits](https://www.conventionalcommits.org/) (`feat(engine): respect owned categories`).
3. Run the checks in [docs/RUNBOOK.md](../docs/RUNBOOK.md#checks) before pushing.
4. Open a PR using the template. CI must be green. **The owner merges; agents never merge.**

## Ground rules
- Never commit `.env` files, keys, raw API responses or personal photos. The pre-commit hook enforces this; enable it with `git config core.hooksPath .githooks`. Never use `--no-verify`.
- No live YouCam calls in tests or CI.
- Copy must stay cosmetic, never medical. Products are labelled "GlowCue Demo".
- Keep `docs/PROJECT_STATUS.md` truthful.

See [AGENTS.md](../AGENTS.md) for the shared conventions and [docs/README.md](../docs/README.md) for the knowledge base.
