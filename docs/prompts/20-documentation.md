# 20: Documentation and README

**Branch:** `chore/release` · **Phase:** 6 · **Depends on:** 18

## Objective
A judge-ready README and accurate docs that describe what is **actually implemented**.

## Context
`docs/SUBMISSION_CHECKLIST.md` §15 (README outline), `.claude/rules/documentation.md`, `docs/PROJECT_STATUS.md`.

## Instructions
1. Rewrite `README.md` with:
   - title and tagline;
   - hero screenshot;
   - live URL and YouTube link;
   - the problem;
   - what it does (the four differentiators);
   - **how YouCam is used** (v2.1 SD, endpoints, 10 concerns, raw vs ui score, masks, task deletion, credit guard, recorded-sample mode);
   - the architecture diagram (Mermaid from `docs/ARCHITECTURE.md`);
   - an engine summary;
   - quick start in **mock mode, no key needed**, and how to enable live mode;
   - an env var table;
   - tests;
   - privacy and safety;
   - the cosmetic disclaimer and demo-catalogue disclaimer;
   - limitations (single photo, lighting, skin-tone performance not independently validated);
   - roadmap, licence and acknowledgements (fonts, icons, YouCam).
2. Audit the docs. Anything planned but not built must be marked as planned. Update API_CONTRACTS, DATA_MODEL and ARCHITECTURE to match the code.
3. Fresh-clone test: clone into a temp dir, follow the README quick start in mock mode, and record the result.
4. Run `python scripts/validate_project.py` (links) and the secret scan.

## Expected files
`README.md`, updated `docs/*.md`.

## Constraints
No claims beyond the evidence. No secrets or unapproved faces in screenshots.

## Acceptance criteria
Fresh-clone quick start works. The validator passes. Every README claim maps to implemented behaviour.

## Required tests
Fresh-clone run, validator, secret scan.

## Definition of completion
Report. PR via prompt 19.
