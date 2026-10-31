"""Claude Code PreToolUse guard for file writes (Write, Edit, MultiEdit, NotebookEdit).

DENY  (exit 2): the target is ANY environment file (.env, .env.local, live.env, ...; .env.example is fine), or the
                new content contains something that looks like a secret. Ordinary approval cannot override.
ASK   (exit 0 + JSON permissionDecision "ask"): the target is a guardrail file (hooks, settings, git hooks, secret
                scanner, guard tests, project validator, CI workflows, .gitignore). The OWNER gets a permission
                prompt, so an agent cannot weaken the guards without a human decision.
Fail closed: unparseable input, unexpected shapes, internal errors and a missing pattern module all produce
"ask" (or "deny" when a secret is visible), never a silent allow. settings.json adds onFailure "block" and
`|| exit 2` so a crash or missing interpreter also blocks the edit.

Shell-based modification of the same files is covered separately in guard_bash.py.
"""

from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

PROJECT_DIR = Path(os.environ.get("CLAUDE_PROJECT_DIR") or Path(__file__).resolve().parents[2])
sys.path.insert(0, str(PROJECT_DIR / "scripts" / "security"))
try:
    from secret_patterns import PROTECTED_PATH_PATTERNS, scan_text

    DEGRADED = False
except Exception:  # fail closed: without the shared patterns every edit needs approval
    DEGRADED = True
    PROTECTED_PATH_PATTERNS = ()

    def scan_text(text):  # type: ignore[no-redef]
        return [1] if re.search(r"\bsk-[A-Za-z0-9_\-]{32,}", text) else []


# Any env-style file: .env, .env.local, live.env, prod.env ... but not *.env.example
ENV_FILE = re.compile(r"(^|[\\/])[^\\/]*\.env(\.(?!example$)[^\\/]+)?$", re.I)


def collect_new_text(tool_input: dict) -> str:
    parts: list[str] = []
    for key in ("content", "new_string", "new_source"):
        if isinstance(tool_input.get(key), str):
            parts.append(tool_input[key])
    for edit in tool_input.get("edits") or []:
        if isinstance(edit, dict) and isinstance(edit.get("new_string"), str):
            parts.append(edit["new_string"])
    return "\n".join(parts)


def decide(tool_input: dict) -> tuple[str, str]:
    path = str(tool_input.get("file_path") or tool_input.get("notebook_path") or "")
    if ENV_FILE.search(path):
        return "deny", "agents never write env files; the owner edits backend/.env personally"
    findings = scan_text(collect_new_text(tool_input))
    if findings:
        rules = ", ".join(sorted({getattr(f, "rule", "secret") for f in findings}))
        return "deny", f"content looks like a secret ({rules}). Use env vars via app/config.py; never hardcode keys"
    if DEGRADED:
        return "ask", "the guard's shared pattern module is unavailable, so this edit can't be checked"
    if any(p.search(path) for p in PROTECTED_PATH_PATTERNS):
        return (
            "ask",
            "this edits a guardrail file (hooks, settings, git hooks, secret scanner, guard tests, validator, CI or "
            ".gitignore). Approve only if you requested it",
        )
    return "allow", ""


def ask(reason: str) -> None:
    print(
        json.dumps(
            {
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": "ask",
                    "permissionDecisionReason": f"GlowCue guard: {reason}",
                }
            }
        )
    )
    sys.exit(0)


def block(reason: str) -> None:
    print(f"BLOCKED by GlowCue edit guard: {reason}.", file=sys.stderr)
    sys.exit(2)


def main() -> None:
    try:
        data = json.loads(sys.stdin.read())
    except Exception:
        ask("the hook input could not be parsed, so this edit can't be checked")
    try:
        tool_input = data.get("tool_input") if isinstance(data, dict) else None
        if not isinstance(tool_input, dict):
            ask("the hook input had an unexpected shape, so this edit can't be checked")
        verdict, reason = decide(tool_input)
    except Exception as exc:  # never fail open
        ask(f"the guard hit an internal error ({type(exc).__name__}); treating this edit as needing approval")
    if verdict == "deny":
        block(reason)
    if verdict == "ask":
        ask(reason)
    sys.exit(0)


if __name__ == "__main__":
    main()
