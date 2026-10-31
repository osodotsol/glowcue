# ADR-002: YouCam API integration approach

- **Status:** Accepted, 31 Oct 2026. Items marked [U] are resolved by the owner-approved probe in Phase 2.

## Context
The hackathon requires a working integration of at least one YouCam API. The owner has 1,000 units, and each analysis costs about 14. Judges must be able to test until 20 Nov without us publishing a key. The organiser confirmed on the forum that a labelled replay of a recorded real response is acceptable.

## Options considered
1. **Skin Analysis v2.1 SD vs HD:** HD needs a short side of at least 1080 px (many laptop webcams are 720p) and costs more. SD needs at least 480 px.
2. **Result format JSON vs ZIP:** JSON returns scores and mask URLs inline. ZIP needs extracting.
3. **Completion: polling vs webhooks:** webhooks need a public endpoint and signature verification.
4. **Input: File API upload vs public image URL:** a public URL would mean hosting user photos.
5. **Visualisation: per-concern PNG masks vs a single blended overlay.**
6. **Judge access: live only vs recorded sample plus capped live.**

## Decision
SD with 10 concerns (14 units). `format: "json"`. **Polling** (≥ 2 s, 90 s timeout). **File API** upload, never public URLs. **Per-concern masks** (`enable_mask_overlay: false`), downloaded server-side and returned as data URLs, then the YouCam task is deleted if verified. **Mock mode by default**, plus a public **recorded-sample mode** and **capped live mode** (per-IP and global caps, a credit floor, a kill switch). Rank on `raw_score` and show `ui_score` only with an honesty note.

## Reason
Maximum robustness and privacy for minimum units, in line with the organiser's guidance on judge testing.

## Consequences
- One owner-approved live probe is needed early to capture the fixture and resolve the [U] items: `skin_type` shape, mask format and size, whether delete works, actual unit cost.
- Every live call needs the **owner's approval in a Claude Code permission prompt**. The command guard returns `"ask"`, and in auto mode a hook "ask" goes to the human, not the classifier.
- *Amended 31 Oct 2026 (PR #1 review, High finding):* the original design used an approval token (`GLOWCUE_LIVE_APPROVED=1`) in the command. The agent could type that itself, so it was a speed bump, not a gate, and it was removed.
- *Amended 31 Oct 2026 (second adversarial review, commit b5a4362):* the first `"ask"` gate only recognised a network program as the first word of a command, so wrappers, nested shells and config-driven calls bypassed it. The hook is now **default-ask** (any YouCam marker in a command that can execute, unless provably inert), reads executed files and local imports, and fails closed. Because command inspection can never be complete, the **backend must enforce live mode itself**: `backend/.env` is authoritative for `YOUCAM_MODE`/`LIVE_ANALYSIS_ENABLED`, all traffic goes through one choke point that checks every condition, and mock mode never builds a real transport (requirements B1-B6 in `docs/SECURITY_PRIVACY.md` §4.4). Backend tests are isolated from the real key and the network.
