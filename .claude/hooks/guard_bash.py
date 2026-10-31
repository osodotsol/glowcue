"""Claude Code PreToolUse guard for Bash and PowerShell commands.

Exit code 2 blocks the command; stderr is shown to Claude, which must then ask the owner.
Deterministic rules only. Permission deny rules in .claude/settings.json are the first layer;
this hook covers command shapes that permission rules cannot express.
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
try:
    from secret_patterns import scan_text
except ImportError:  # never fail open silently on secrets: fall back to a minimal pattern

    def scan_text(text):  # type: ignore[no-redef]
        return [1] if re.search(r"\bsk-[A-Za-z0-9_\-]{32,}", text) else []


LIVE_TOKEN = "GLOWCUE_LIVE_APPROVED=1"

# .env / .env.local / .env.production … but not .env.example
ENV_FILE = re.compile(r"(?<![\w-])\.env(?:\.(?!example\b)[\w-]+)?(?![\w.-])")
# Commands that read, copy or load a file. Matched only as the *command word* of a segment, so prose
# such as a commit message mentioning ".env files" is not a false positive.
ENV_READERS = re.compile(
    r"^(cat|type|less|more|head|tail|bat|nl|od|xxd|strings|grep|egrep|rg|findstr|sed|awk|cut|sort|uniq|"
    r"Get-Content|gc|Select-String|cp|copy|Copy-Item|mv|move|Move-Item|scp|rsync|curl|base64|source|\.|"
    r"python\S*|py|node|vim?|nano|code|notepad\S*|dotenv)$",
    re.I,
)
# Programs that could send a request to the YouCam API host.
NETWORK_COMMANDS = re.compile(
    r"^(\S*[\\/])?(python\S*|py|uvicorn|curl|wget|http|https|node|npx|deno|bun|"
    r"Invoke-WebRequest|Invoke-RestMethod|iwr|irm)$",
    re.I,
)
LIVE_TARGET = re.compile(r"makeupar\.com|yce-api|probe_youcam", re.I)
SEGMENT_SPLIT = re.compile(r"\n|;|&&|\|\||\||\$\(|`")
ASSIGNMENT = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*=")


def segments(cmd: str) -> list[tuple[list[str], str, str]]:
    """Split a shell command into simple commands: (env assignments, command word, full segment text)."""
    out = []
    for raw in SEGMENT_SPLIT.split(cmd):
        words = raw.strip().split()
        assigns = []
        while words and ASSIGNMENT.match(words[0]):
            assigns.append(words.pop(0))
        if words and words[0] in {"sudo", "env", "exec", "time", "nohup", "&"}:
            words.pop(0)
        if words:
            out.append((assigns, words[0].strip("\"'()"), raw))
    return out


RULES: list[tuple[re.Pattern[str], str]] = [
    (
        re.compile(r"\bprintenv\b|(^|[;&|]\s*)env\s*($|[|;&>])|Get-ChildItem\s+env:|\bls\s+env:|\bdir\s+env:", re.I),
        "dumping environment variables could print the YouCam key",
    ),
    (re.compile(r"(\$\{?|\$env:)YOUCAM_API_KEY", re.I), "commands must never expand or print YOUCAM_API_KEY"),
    (
        re.compile(r"\bgit\s+add\b[^;&|]*\s(-f|--force)\b"),
        "force-adding ignored files is not allowed (they are ignored for a reason)",
    ),
    (re.compile(r"\bgit\s+add\b[^;&|]*" + ENV_FILE.pattern), ".env files must never be staged"),
    (
        re.compile(r"\bgit\s+(commit|push|merge|rebase)\b[^;&|]*--no-verify\b"),
        "skipping git hooks (--no-verify) is not allowed",
    ),
    (
        re.compile(r"\bgit\s+push\b[^;&|]*(\s-f\b|--force|\s\+\S)"),
        "force-push requires explicit owner approval; ask the owner to run it",
    ),
    (re.compile(r"\bgit\s+push\b[^;&|]*(--delete|\s:\S)"), "deleting remote branches requires owner approval"),
    (
        re.compile(
            r"\bgit\s+reset\s+--hard\b|\bgit\s+clean\s+-[a-zA-Z]*f|\bgit\s+checkout\s+--\s+\.|\bgit\s+restore\s+\.(\s|$)"
        ),
        "destructive working-tree reset; ask the owner to run it if really needed",
    ),
    (re.compile(r"\bgh\s+pr\s+merge\b"), "merging PRs requires explicit owner approval; the owner merges"),
    (
        re.compile(r"\bgh\s+repo\s+(delete|edit|rename|archive)\b"),
        "changing repository settings requires owner approval",
    ),
    (
        re.compile(
            r"\brm\s+(-[a-zA-Z]*r[a-zA-Z]*f|-[a-zA-Z]*f[a-zA-Z]*r)\s+(/|~|\$HOME|\.git\b|\*|\.\.?(\s|$)|[A-Za-z]:[\\/]?(\s|$))"
        ),
        "recursive delete of a root, home, .git or wildcard path",
    ),
    (
        re.compile(r"Remove-Item\b[^;&|]*-Recurse[^;&|]*(\s[A-Za-z]:\\?(\s|$)|\s~|\s\.git\b|\s\*)", re.I),
        "recursive delete of a root, home, .git or wildcard path",
    ),
]


def block(reason: str) -> None:
    print(
        f"BLOCKED by GlowCue command guard: {reason}. Do not retry a variant; explain and ask the owner.",
        file=sys.stderr,
    )
    sys.exit(2)


def main() -> None:
    try:
        data = json.load(sys.stdin)
    except json.JSONDecodeError:
        sys.exit(0)
    cmd = (data.get("tool_input") or {}).get("command") or ""
    flat = " ".join(cmd.split())

    approved = LIVE_TOKEN in cmd
    for assigns, word, text in segments(cmd):
        reads_env = ENV_FILE.search(text) and (ENV_READERS.match(word) or re.search(r"<\s*\S*\.env\b", text))
        if reads_env:
            block("reading or copying a .env file could expose the YouCam key (only the owner opens backend/.env)")
        # Quota guard: live YouCam traffic requires the owner's approval token in the command itself.
        live_mode = any(a.upper().startswith("YOUCAM_MODE=LIVE") for a in assigns)
        live_call = NETWORK_COMMANDS.match(word) and LIVE_TARGET.search(text)
        if (live_mode or live_call) and not approved:
            block(f"live YouCam calls consume units; get owner approval, then prefix the command with {LIVE_TOKEN}")

    for pattern, reason in RULES:
        if pattern.search(flat):
            block(reason)

    if scan_text(cmd):
        block("the command contains what looks like a secret value")

    sys.exit(0)


if __name__ == "__main__":
    main()
