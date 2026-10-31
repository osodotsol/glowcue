# Test Plan

> **Status:** planned design from the GlowCue blueprint (research snapshot 31 Oct 2026). Nothing here is implemented unless [PROJECT_STATUS](PROJECT_STATUS.md) says so. Tags: **[V]** verified, **[A]** assumption, **[R]** recommendation, **[U]** unresolved.

## 13. Testing & QA

| Level | What | Tool | Gate |
|---|---|---|---|
| Unit (backend) | normaliser, catalogue validator, engine, routine, image validation, limits, YouCam client (mocked transport) | pytest | Green; engine ≥ 90% coverage |
| API | every route, mock mode, error envelopes, CORS, consent required | FastAPI TestClient | Green |
| Frontend unit | `imagePrep`, formatters | Vitest | Green |
| Mock-mode e2e | full journey | Playwright smoke | Green before every deploy |
| Live verification | 1 local (Phase 6) + 1 prod (Phase 9) + 1 final (Mon 12:00) | Manual | Balance decreases by 14 each |
| Failure scenarios | listed in [prompt 16](prompts/16-testing.md) | Manual + tests | Each shows the correct UI |
| Security | secret scan, headers, limits | grep, `pip-audit`, `npm audit`; GitHub push protection (on by default for public repos) | No high findings |
| Privacy | EXIF absent (check with an online-free local tool such as `exiftool` or Pillow), no images in logs or disk, clear-data works | Manual | Pass |
| Mobile | real phone on mobile data: Android Chrome + iOS Safari if available | Manual + Antigravity viewports | No P0/P1 |
| Accessibility | keyboard-only run, Lighthouse a11y ≥ 95, contrast | Lighthouse | Pass |

---
