"""Owner-approved YouCam probe: ONE live skin analysis through GlowCue's own client and safeguards.

Run ONLY after the owner approves it in chat; the command guard will also show a permission prompt.
Live mode must be switched on by the owner in backend/.env (YOUCAM_MODE=live, LIVE_ANALYSIS_ENABLED=true,
YOUCAM_API_KEY=...). This script never prints the key.

    # 1) free: confirm the key works and read the balance (no task is created)
    backend/.venv/Scripts/python backend/scripts/probe_youcam.py --balance-only
    # 2) error path: a synthetic face-free image; expected to fail with no units charged
    backend/.venv/Scripts/python backend/scripts/probe_youcam.py --no-face --spend-units
    # 3) one real analysis of a consenting adult's selfie (about 14 units on success)
    backend/.venv/Scripts/python backend/scripts/probe_youcam.py path/to/selfie.jpg --spend-units

What it records (printed, and saved to the gitignored backend/app/fixtures/raw/):
  balance before/after and the delta, elapsed time, task outcome, which output types came back, whether
  items carry a region, the normalised GlowCue scores, and the result with every URL and identifier removed
  (sanitised only at the moment the file is written; the in-memory response is never modified).
"""

from __future__ import annotations

import argparse
import asyncio
import io
import json
import re
import sys
import time
from datetime import UTC, datetime
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))

from PIL import Image  # noqa: E402

from app.config import get_settings  # noqa: E402
from app.services.image import prepare_image  # noqa: E402
from app.services.normalize import SD_ACTIONS, normalise_items  # noqa: E402
from app.services.youcam_client import UNVERIFIED, YouCamClient, YouCamError, live_refusal  # noqa: E402

RAW_DIR = BACKEND / "app" / "fixtures" / "raw"  # gitignored


# Identifier fields: "id" itself, or any key ending in "_id" (task_id, file_id, dst_id, request_id, ...).
_ID_KEY = re.compile(r"^id$|_id$", re.IGNORECASE)


def sanitise_for_saving(value: object) -> object:
    """Return a NEW copy that is safe to save; `value` itself is never modified.

    Removes identifier fields (see _ID_KEY) at every level, replaces any field whose name contains "url" and any
    string starting with "http" with "<removed>". Everything else is kept as is: concern types, raw/ui scores,
    regions, overall scores and other analysis metadata.
    """
    if isinstance(value, dict):
        copy: dict[object, object] = {}
        for key, item in value.items():
            name = str(key)
            if _ID_KEY.search(name):
                continue
            copy[key] = "<removed>" if "url" in name.lower() else sanitise_for_saving(item)
        return copy
    if isinstance(value, list):
        return [sanitise_for_saving(item) for item in value]
    if isinstance(value, str) and value.startswith("http"):
        return "<removed>"
    return value


def save_outcome(outcome: dict[str, object], raw_dir: Path = RAW_DIR) -> Path:
    """The file-saving boundary: only here is a sanitised copy made, and only the copy is written."""
    raw_dir.mkdir(parents=True, exist_ok=True)
    path = raw_dir / f"probe-{datetime.now(UTC):%Y%m%dT%H%M%SZ}.raw.json"
    path.write_text(json.dumps(sanitise_for_saving(outcome), indent=2), encoding="utf-8")
    return path


def _no_face_image() -> bytes:
    buf = io.BytesIO()
    Image.linear_gradient("L").resize((720, 960)).convert("RGB").save(buf, "JPEG")
    return buf.getvalue()


async def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("photo", nargs="?", type=Path, help="selfie (JPEG/PNG) of a consenting adult")
    parser.add_argument("--balance-only", action="store_true", help="read the unit balance only (free)")
    parser.add_argument("--no-face", action="store_true", help="send a synthetic face-free image (error path)")
    parser.add_argument("--spend-units", action="store_true", help="required for any task-creating run")
    args = parser.parse_args()

    settings = get_settings()
    refusal = live_refusal(settings)
    if refusal:
        print(f"Refused: {refusal}. The owner switches live mode on in backend/.env.")
        return 2
    print(f"Task API {settings.youcam_task_api}; actions: {', '.join(SD_ACTIONS)}")
    print("Unverified assumptions this run checks:", *UNVERIFIED, sep="\n  - ")

    async with YouCamClient(settings) as client:
        before = await client.credit_balance()
        print(f"Balance before: {before}")
        if args.balance_only:
            return 0
        if not args.spend_units:
            print("Refused: add --spend-units to confirm this run may create a task (about 14 units on success).")
            return 2
        if args.no_face:
            data = _no_face_image()
        elif args.photo:
            data = args.photo.read_bytes()
        else:
            parser.error("give a photo path, or --no-face, or --balance-only")
        image = prepare_image(data)  # same validation and EXIF removal as the app
        started = time.monotonic()
        outcome: dict[str, object] = {"when_utc": datetime.now(UTC).isoformat(timespec="seconds")}
        try:
            items = await client.analyse_skin(image.data, image.content_type, SD_ACTIONS)
            outcome["status"] = "success"
            outcome["types"] = sorted({i.type for i in items})
            outcome["regions"] = sorted({i.region for i in items if i.region})
            normalised = normalise_items(items)
            outcome["glowcue_scores"] = normalised.scores
            outcome["ignored_types"] = list(normalised.ignored_types)
            outcome["result"] = client.last_result  # the original response, untouched; sanitised only when saved
        except YouCamError as exc:
            outcome["status"] = "error"
            outcome["error_code"] = exc.code
            outcome["http_status"] = exc.http_status
        outcome["elapsed_s"] = round(time.monotonic() - started, 1)
        after = await client.credit_balance()
        outcome["balance_before"], outcome["balance_after"] = before, after
        outcome["units_used"] = round(before - after, 2)

    print(json.dumps({k: v for k, v in outcome.items() if k != "result"}, indent=2))
    out = save_outcome(outcome)  # the task was already deleted inside analyse_skin(), using the in-memory task id
    print(f"Saved (gitignored): {out.relative_to(BACKEND.parent)}")
    print("Record the date, purpose, unit delta and result in docs/YOUCAM_API.md 6.8.")
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
