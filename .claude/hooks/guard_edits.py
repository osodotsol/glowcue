"""Claude Code PreToolUse guard for file writes (Write, Edit, MultiEdit, NotebookEdit).

Blocks (exit 2) when:
  - the target is a real environment file (.env, .env.local, …), or
  - the new content contains something that looks like a secret.
"""

from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

sys.path.insert(
    0, str(Path(os.environ.get("CLAUDE_PROJECT_DIR", Path(__file__).resolve().parents[2])) / "scripts" / "security")
)
from secret_patterns import scan_text  # noqa: E402

ENV_FILE = re.compile(r"(^|[\\/])\.env(\.(?!example$)[^\\/]+)?$")


def collect_new_text(tool_input: dict) -> str:
    parts: list[str] = []
    for key in ("content", "new_string", "new_source"):
        if isinstance(tool_input.get(key), str):
            parts.append(tool_input[key])
    for edit in tool_input.get("edits") or []:
        if isinstance(edit, dict) and isinstance(edit.get("new_string"), str):
            parts.append(edit["new_string"])
    return "\n".join(parts)


def main() -> None:
    try:
        data = json.load(sys.stdin)
    except json.JSONDecodeError:
        sys.exit(0)
    tool_input = data.get("tool_input") or {}
    path = str(tool_input.get("file_path") or tool_input.get("notebook_path") or "")
    if ENV_FILE.search(path):
        print(
            "BLOCKED by GlowCue edit guard: agents never write .env files; the owner edits backend/.env personally.",
            file=sys.stderr,
        )
        sys.exit(2)
    findings = scan_text(collect_new_text(tool_input))
    if findings:
        rules = ", ".join(sorted({f.rule for f in findings}))
        print(
            f"BLOCKED by GlowCue edit guard: content looks like a secret ({rules}). "
            "Use env vars via app/config.py; never hardcode keys.",
            file=sys.stderr,
        )
        sys.exit(2)
    sys.exit(0)


if __name__ == "__main__":
    main()
