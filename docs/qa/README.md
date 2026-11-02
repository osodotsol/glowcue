# QA reports

Antigravity owns this folder; Claude Code reads it. Files:
- `AG-REPORT-<n>.md`: Antigravity browser reviews (rules: `.agents/rules/antigravity-reviewer.md`)
- `DESIGN-REVIEW-<n>.md`: output of the `/design-review` skill
- `SECURITY-REVIEW-<date>.md`: output of the `/security-review` skill
- `screens/`: screenshots referenced by reports (no faces without consent, no keys)

## Report template
```markdown
# AG-REPORT-<n>: <scope>
Checkpoint commit: <sha>   Date (WAT): <date time>   URL: <url>   Mode: mock | sample | deployed

| # | Sev | Screen | Viewport | Steps | Expected | Actual | Screenshot |
|---|-----|--------|----------|-------|----------|--------|------------|
| 1 | P1  | Results | 375 | Open sample → Results | Heatmap aligned | Mask offset ~12px | screens/ag1-01.png |

## Top 5 fixes (ranked by user + judging impact)
1. …
```
Severity: **P0** blocks the journey · **P1** visibly broken or inaccessible · **P2** polish · **P3** nice-to-have.
