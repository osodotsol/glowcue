# Security & privacy rules (always loaded)

## Credentials
- The YouCam key is read **only** through `backend/app/config.py` (pydantic-settings, env var `YOUCAM_API_KEY`). It must never appear in Python literals, frontend code, `VITE_*` variables, HTML, docs, screenshots, test fixtures, CI logs or commit messages.
- Never open, print, copy or `source` `backend/.env`. Permission rules and hooks enforce this. If a key is needed, ask the owner to put it in `.env`.
- The first key was exposed in a chat transcript. Treat any key seen in conversation as compromised: tell the owner to rotate it, and never reuse it.
- In logs, error messages and exception reprs, redact the `Authorization` header and never include request bodies containing image bytes.

## Photographs
- Uploads stay in memory (`bytes`). Never write them to disk, temp files, logs or caches.
- Strip metadata (EXIF and GPS) on the client (canvas re-encode) **and** on the server (Pillow re-encode).
- Require `consent=true`. Reject requests without it before touching the image.
- Keep results in an in-memory TTL store (30 min). After results are retrieved, delete the YouCam task when that's verified to work (see `docs/YOUCAM_API.md`).
- Never commit photos. The pre-commit hook blocks `.jpg/.jpeg/.heic/.webp` outside approved folders. A sample photo needs explicit owner approval (`GLOWCUE_PHOTO_APPROVED=1`).

## Web security
- CORS allows only `FRONTEND_ORIGIN` (plus localhost in development).
- Server-side limits: 10 MB upload, accepted MIME types `image/jpeg` and `image/png`, a per-IP daily cap, a global daily cap, a credit floor, and a `LIVE_ANALYSIS_ENABLED` kill switch.
- Never fetch a URL supplied by the user (SSRF). The only outbound hosts are the YouCam API host and the presigned upload and mask URLs it returns.
- Never trust client prices. Cart totals are recomputed server-side from the catalogue.

## Dependencies
- Pin versions (`requirements*.txt` with `==`, plus `package-lock.json`). Run `npm audit --omit=dev` and review new packages before adding them.
