# 10: Image upload and consent

**Branch:** `feat/frontend-experience` · **Phase:** 4 · **Skill:** `/frontend-engineering` · **Depends on:** 08, 02

## Objective
A guided, privacy-respecting photo capture and upload screen that only submits valid, consented, EXIF-free images.

## Context
`docs/DESIGN_SYSTEM.md` §8.3 (Analyse row), `docs/PRD.md` F2, `docs/YOUCAM_API.md` §6.1 (specs and photo tips), `docs/SECURITY_PRIVACY.md` §3.

## Instructions
1. `lib/imagePrep.ts`:
   - `prepareImage(file): Promise<{blob, width, height, previewUrl}>`;
   - accept `image/jpeg` and `image/png`, under 10 MB;
   - decode with `createImageBitmap(file, {imageOrientation: "from-image"})`;
   - reject a short side under 480 px;
   - scale the long side to at most 2048;
   - `canvas.toBlob("image/jpeg", 0.9)`.

   Typed errors: `unsupported_type`, `too_large`, `too_small`, `decode_failed`.
2. `pages/Analyze.tsx`:
   - photo tips (light, face fills frame, hair off forehead, no glasses or makeup, look straight);
   - a dropzone plus a file input with `accept="image/jpeg,image/png"` and a mobile camera button (`capture="user"`);
   - a preview with an oval guide;
   - a **consent checkbox** (required) with a privacy summary and a link to the policy text;
   - the **Analyse** button is disabled until the image is valid and consent is given.
3. Submit `multipart/form-data` (`image`, `consent=true`) through `api.createAnalysis()`, then navigate to `/processing/:id`. Map backend errors (403 live disabled or capped) to friendly copy with a "Use the recorded sample instead" action.
4. Revoke object URLs on unmount. Never store the image in `sessionStorage`.
5. Add Vitest (`npm i -D vitest jsdom`, ask first) and a `test` script. Unit-test `imagePrep` with synthetic canvases or blobs.

## Expected files
`frontend/src/lib/imagePrep.ts`, `frontend/src/lib/imagePrep.test.ts`, `frontend/src/pages/Analyze.tsx`, `frontend/src/lib/api.ts`, `frontend/package.json`, `frontend/vite.config.ts` (test config).

## Constraints
No third-party upload services. No face-detection libraries (YouCam validates faces). Keep it lean.

## Acceptance criteria
A GIF, an 11 MB file and a 300 px image are each rejected with a specific message. A valid JPEG produces a ≤ 2048 px blob with no EXIF. Submitting without consent is impossible.

## Required tests
Vitest: type, size and dimension rejections, plus resize output dimensions.

## Definition of completion
`npm run test`, lint, typecheck and build green. Report.
