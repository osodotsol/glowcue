"""Claude Code PreToolUse guard for Bash and PowerShell commands.

Three outcomes, in precedence order:
  1. DENY  (exit 2, reason on stderr): dangerous or secret-exposing commands. Claude must explain and ask the owner.
  2. ASK   (exit 0, JSON permissionDecision "ask"): commands that could spend YouCam units, or that modify the
           guardrail files themselves. Claude Code shows the OWNER a permission prompt; in auto mode the
           classifier does not decide hook "ask" decisions (docs: hooks → "PreToolUse ask decisions in auto mode").
           There is deliberately NO token or variable that lets the agent pre-approve itself.
  3. ALLOW (exit 0, no output): everything else, subject to the normal permission rules.

Deterministic, best-effort rules: permission deny rules in .claude/settings.json are the first layer.
"""

from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

PROJECT_DIR = Path(os.environ.get("CLAUDE_PROJECT_DIR", Path(__file__).resolve().parents[2]))
sys.path.insert(0, str(PROJECT_DIR / "scripts" / "security"))
try:
    from secret_patterns import scan_text
except ImportError:  # never fail open silently on secrets: fall back to a minimal pattern

    def scan_text(text):  # type: ignore[no-redef]
        return [1] if re.search(r"\bsk-[A-Za-z0-9_\-]{32,}", text) else []


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
YOUCAM_HOST = re.compile(r"makeupar\.com|yce-api", re.I)
LIVE_SCRIPT = re.compile(r"probe_youcam", re.I)
# Switching the backend to live mode from the command line (bash assignment/export, PowerShell $env:).
LIVE_MODE = re.compile(r"YOUCAM_MODE\s*=\s*['\"]?live\b", re.I)
# Code that would talk to YouCam if executed (checked inside Python script files passed as arguments).
SCRIPT_LIVE_MARKERS = re.compile(r"makeupar\.com|yce-api|youcam_client|probe_youcam", re.I)

# Guardrail files: changing them must always be a human decision.
PROTECTED_PATHS = re.compile(
    r"\.claude[\\/](hooks[\\/]|settings(\.local)?\.json)|\.githooks[\\/]|scripts[\\/]security[\\/]", re.I
)
WRITE_OPERATIONS = re.compile(
    r"(^|\s)(>>?|tee\b|sed\s+-i|perl\s+-[a-z]*i|cp\b|mv\b|rm\b|truncate\b|chmod\b|Set-Content|Add-Content|"
    r"Out-File|Remove-Item|Copy-Item|Move-Item|git\s+(checkout|restore|rm|mv)\b)",
    re.I,
)

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


def ask(reason: str) -> None:
    """Hand the decision to the human: Claude Code shows the owner a permission prompt with this reason."""
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


def script_runs_youcam(text: str, cwd: Path) -> bool:
    """True when a .py file passed on this command line contains code that could call YouCam."""
    if re.search(r"-m\s+pytest\b|(^|\s)pytest\b", text):
        return False  # tests mock all HTTP (testing rules); never prompt for them
    for token in re.findall(r"[^\s\"']+\.py\b", text):
        path = Path(token)
        if not path.is_absolute():
            path = cwd / path
        try:
            if path.is_file() and SCRIPT_LIVE_MARKERS.search(
                path.read_text(encoding="utf-8", errors="ignore")[:300_000]
            ):
                return True
        except OSError:
            continue
    return False


def live_reason(cmd: str, cwd: Path) -> str | None:
    """Return why this command could spend YouCam units, or None."""
    if LIVE_MODE.search(cmd):
        return "this command switches the backend to YOUCAM_MODE=live, which can spend YouCam units"
    segs = segments(cmd)
    runs_network_program = any(NETWORK_COMMANDS.match(word) for _a, word, _t in segs)
    # Checked against the WHOLE command: quoted code such as `python -c "a; httpx.get(...)"` is split
    # on `;` by the segmenter, so the host can land in a different segment from the program.
    if runs_network_program and (YOUCAM_HOST.search(cmd) or LIVE_SCRIPT.search(cmd)):
        return "this command contacts the YouCam API (may spend units; even free calls need your OK)"
    for _assigns, word, text in segs:
        if LIVE_SCRIPT.search(word):
            return "this runs the YouCam probe script, which spends YouCam units"
        if NETWORK_COMMANDS.match(word) and script_runs_youcam(text, cwd):
            return "this runs a script containing YouCam API code, which may spend units"
    return None


def main() -> None:
    try:
        data = json.load(sys.stdin)
    except json.JSONDecodeError:
        sys.exit(0)
    cmd = (data.get("tool_input") or {}).get("command") or ""
    cwd = Path(data.get("cwd") or os.getcwd())
    flat = " ".join(cmd.split())

    # 1. DENY rules always win.
    for _assigns, word, text in segments(cmd):
        if ENV_FILE.search(text) and (ENV_READERS.match(word) or re.search(r"<\s*\S*\.env\b", text)):
            block("reading or copying a .env file could expose the YouCam key (only the owner opens backend/.env)")
    for pattern, reason in RULES:
        if pattern.search(flat):
            block(reason)
    if scan_text(cmd):
        block("the command contains what looks like a secret value")

    # 2. ASK: unit-spending calls and changes to the guardrails need a real human prompt.
    reason = live_reason(cmd, cwd)
    if reason:
        ask(reason + ". Approve only if you asked for this specific live call.")
    if PROTECTED_PATHS.search(cmd) and WRITE_OPERATIONS.search(cmd):
        ask("this command modifies GlowCue guardrail files (hooks, settings, git hooks or secret scanner)")

    # 3. ALLOW (normal permission rules still apply).
    sys.exit(0)


if __name__ == "__main__":
    main()
