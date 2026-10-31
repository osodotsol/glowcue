"""Claude Code PostToolUse hook: format an edited backend/scripts Python file with ruff.

Cheap (one file), never blocks: formatting failures are ignored so editing is never interrupted.
Runs only when the backend virtualenv exists (backend/.venv) and the file is a .py file.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path


def main() -> None:
    try:
        data = json.load(sys.stdin)
    except json.JSONDecodeError:
        return
    path = str((data.get("tool_input") or {}).get("file_path") or "")
    if not path.endswith(".py"):
        return
    root = Path(os.environ.get("CLAUDE_PROJECT_DIR", Path(__file__).resolve().parents[2]))
    venv = root / "backend" / ".venv"
    ruff = venv / ("Scripts/ruff.exe" if os.name == "nt" else "bin/ruff")
    if not ruff.exists():
        return
    config = root / "ruff.toml"
    subprocess.run([str(ruff), "format", "--config", str(config), path], capture_output=True, timeout=25)


if __name__ == "__main__":
    try:
        main()
    except Exception:  # formatting must never break an edit
        pass
    sys.exit(0)
