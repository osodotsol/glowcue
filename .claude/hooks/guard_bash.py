"""Claude Code PreToolUse guard for Bash / PowerShell commands.

Outcomes, in precedence order (see docs/SECURITY_PRIVACY.md for what is and is NOT covered):
  1. DENY  (exit 2, reason on stderr): secret-exposing or destructive commands. Ordinary approval cannot override.
  2. ASK   (exit 0 + JSON permissionDecision "ask"): the OWNER gets a real permission prompt for
           - anything that could reach YouCam (spend units) or switch the backend to live mode;
           - anything that could modify a guardrail file (hooks, settings, git hooks, secret scanner, CI, .gitignore).
           In auto mode a hook "ask" goes to the human, not to the classifier. No token or variable pre-approves.
  3. ALLOW (exit 0, no output): everything else, subject to the normal permission rules.

Design: DEFAULT-ASK when a YouCam marker or a guardrail path appears anywhere in a command, unless every
executing part of the command is provably inert (git, echo, cat, grep, ... or a known read-only tool run).
Shell wrappers (bash -c, timeout, xargs, uv run ...) are therefore covered without enumerating them.

Fail closed: unparseable input, unexpected input shapes, internal errors and a missing pattern module all
produce "ask" (or deny for secrets), never a silent allow. settings.json adds onFailure "block" plus
`|| exit 2` so a crash or missing interpreter blocks the command too.

This is a best-effort classifier of command TEXT, not a sandbox. Known limits are listed in SECURITY_PRIVACY.md.
"""

from __future__ import annotations

import json
import os
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

PROJECT_DIR = Path(os.environ.get("CLAUDE_PROJECT_DIR") or Path(__file__).resolve().parents[2])
sys.path.insert(0, str(PROJECT_DIR / "scripts" / "security"))
try:
    from secret_patterns import PROTECTED_PATH_PATTERNS, scan_text

    DEGRADED = False
except Exception:  # fail closed: without the shared patterns every non-trivial command needs approval
    DEGRADED = True
    PROTECTED_PATH_PATTERNS = ()

    def scan_text(text):  # type: ignore[no-redef]
        return [1] if re.search(r"\bsk-[A-Za-z0-9_\-]{32,}", text) else []


# ----------------------------------------------------------------------------- vocabulary
# .env / .env.local / .env.production ... but not .env.example
ENV_FILE = re.compile(r"(?<![\w-])\.env(?:\.(?!example\b)[\w-]+)?(?![\w.-])")
ENV_READERS = re.compile(
    r"^(cat|type|less|more|head|tail|bat|nl|od|xxd|strings|grep|egrep|rg|findstr|sed|awk|cut|sort|uniq|"
    r"get-content|gc|select-string|cp|copy|copy-item|mv|move|move-item|scp|rsync|curl|base64|source|\.|"
    r"python[\d.]*|py|node|vim?|nano|code|notepad\S*|dotenv|bash|sh|zsh|dash|pwsh|powershell|cmd|eval|xargs|"
    r"uv|uvx|npx|perl|ruby|php|deno|bun)$",
    re.I,
)

# Programs that execute code or make requests. Their file arguments are scanned for YouCam markers.
EXEC_WORDS = re.compile(
    r"^(python[\d.]*|py|pythonw|node|deno|bun|npx|pnpm|yarn|npm|uv|uvx|pipx|poetry|bash|sh|zsh|dash|ksh|fish|"
    r"pwsh|powershell|cmd|curl|wget|http|https|ruby|perl|php|java|dotnet|go|cargo|rscript|osascript|"
    r"invoke-webrequest|invoke-restmethod|iwr|irm|start-process|invoke-expression|iex|eval|source|\.|"
    r"uvicorn|gunicorn|hypercorn)$",
    re.I,
)
# Prefix programs: the real command is the next non-option word.
WRAPPERS = {
    "sudo", "doas", "env", "exec", "time", "nohup", "timeout", "nice", "ionice", "command", "builtin", "xargs",
    "stdbuf", "setsid", "watch", "caffeinate", "start", "call", "chroot", "unbuffer", "winpty", "then", "do",
    "else", "if", "while", "until", "for",
}  # fmt: skip
# Programs that only print/inspect/move files: a YouCam marker in their text is a mention, not an execution.
INERT_WORDS = {
    "git", "gh", "echo", "printf", "cat", "grep", "egrep", "fgrep", "rg", "ls", "dir", "head", "tail", "wc", "diff",
    "cmp", "mkdir", "cd", "pwd", "true", "false", "test", "[", "sleep", "date", "which", "where", "basename",
    "dirname", "realpath", "stat", "file", "sort", "uniq", "tr", "cut", "touch", "rm", "mv", "cp", "type",
    "get-content", "select-string", "get-childitem", "findstr", "pytest",
}  # fmt: skip
# NOTE: export/set/unset/local are deliberately NOT inert: they change the environment of later commands.
# Commands that cannot modify a file (unless output is redirected): safe to mention guardrail paths.
READONLY_WORDS = {
    "cat", "head", "tail", "less", "more", "grep", "egrep", "fgrep", "rg", "ls", "dir", "wc", "diff", "cmp", "stat",
    "file", "type", "get-content", "select-string", "get-childitem", "findstr", "md5sum", "sha256sum", "sha1sum",
    "realpath", "basename", "dirname", "test", "[", "echo", "printf", "cd", "pwd", "which", "where", "true", "false",
    "sleep", "date",
}  # fmt: skip
# git sub-commands that can rewrite working-tree files or hook configuration.
GIT_MODIFYING = {
    "checkout", "restore", "apply", "am", "rm", "mv", "reset", "stash", "merge", "rebase", "cherry-pick", "pull",
    "switch", "revert", "clean", "update-index", "filter-branch", "replace", "config",
}  # fmt: skip

# YouCam markers in command text (broad: a mention in an executing command needs a human look).
LIVE_MARKERS = re.compile(
    r"makeupar\.com|yce-api|probe_youcam|youcam_client|youcam_base_url|youcam_api_key|get_secret_value",
    re.I,
)
# Markers inside files that a command executes (narrower, so ordinary imports of app.config do not match).
FILE_MARKERS = re.compile(
    r"makeupar\.com|yce-api|probe_youcam|youcam_client|youcam_base_url|youcam_api_key|get_secret_value", re.I
)
# Anything that could switch the backend to live mode from the command line.
MODE_MARKERS = re.compile(r"YOUCAM_MODE|LIVE_ANALYSIS_ENABLED|SetEnvironmentVariable|--env-file|env_file|dotenv", re.I)
MODE_MOCK_OK = re.compile(r"YOUCAM_MODE\s*=\s*['\"]?mock\b", re.I)
HEREDOC = re.compile(r"(?<!<)<<-?\s*(['\"]?)([A-Za-z_]\w*)\1")
REDIRECT = re.compile(r"(?<!&)>>?(?!&)\s*(?!/dev/null\b)\S")
ASSIGNMENT = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*=")
BINARY_SUFFIXES = {
    ".png", ".jpg", ".jpeg", ".gif", ".webp", ".ico", ".zip", ".pdf", ".woff", ".woff2", ".exe", ".dll", ".pyc",
}  # fmt: skip
MAX_SCAN_BYTES = 300_000


# ----------------------------------------------------------------------------- tokenizer
@dataclass
class Stmt:
    """One simple command: raw text, shell words (quotes removed), text with quoted content blanked."""

    text: str
    words: list[str]
    unq: str
    body: str = ""  # heredoc body, when this statement owns one
    assigns: list[str] = field(default_factory=list)
    effective: str = ""  # real command word after assignments and wrappers
    args: list[str] = field(default_factory=list)  # words after the effective command

    @property
    def full(self) -> str:
        return self.text + ("\n" + self.body if self.body else "")

    @property
    def has_substitution(self) -> bool:
        return "$(" in self.text or "`" in self.text or "<(" in self.text

    @property
    def redirects(self) -> bool:
        return bool(REDIRECT.search(self.unq))

    @property
    def git_sub(self) -> str | None:
        if self.effective != "git":
            return None
        it = iter(self.args)
        for a in it:
            if a in ("-C", "-c", "--git-dir", "--work-tree", "--namespace"):
                next(it, None)
            elif not a.startswith("-"):
                return a.lower()
        return None


def norm_word(word: str) -> str:
    if word.strip("\"'") in (".", "./"):
        return "."  # the POSIX dot-source command; Path(".").name would be empty
    name = Path(word.replace("\\", "/")).name.lower()
    return re.sub(r"\.(exe|cmd|bat)$", "", name)


def resolve_effective(words: list[str]) -> tuple[list[str], str, list[str]]:
    words = list(words)
    assigns: list[str] = []
    while words and ASSIGNMENT.match(words[0]):
        assigns.append(words.pop(0))
    while words and norm_word(words[0]) in WRAPPERS:
        words.pop(0)
        while words and (
            words[0].startswith("-") or re.fullmatch(r"\d+(\.\d+)?[smhd]?", words[0]) or ASSIGNMENT.match(words[0])
        ):
            words.pop(0)
    if not words:
        return assigns, "", []
    return assigns, norm_word(words[0].strip("\"'()")), words[1:]


def split_heredocs(cmd: str) -> tuple[str, list[str]]:
    """Remove heredoc bodies from the text, returning (command without bodies, bodies in order)."""
    out: list[str] = []
    bodies: list[list[str]] = []
    pending: str | None = None
    for line in cmd.split("\n"):
        if pending is not None:
            bodies[-1].append(line)
            if line.strip() == pending:
                pending = None
            continue
        out.append(line)
        m = HEREDOC.search(line)
        if m:
            pending = m.group(2)
            bodies.append([])
    return "\n".join(out), ["\n".join(b) for b in bodies]


def tokenize(cmd: str) -> list[Stmt]:
    s, bodies = split_heredocs(cmd)
    stmts: list[Stmt] = []
    words: list[str] = []
    word: list[str] = []
    unq: list[str] = []
    in_word = False
    q: str | None = None
    seg_start = 0

    def flush_word() -> None:
        nonlocal in_word
        if in_word:
            words.append("".join(word))
            word.clear()
            in_word = False

    def flush_seg(end: int, next_start: int) -> None:
        nonlocal seg_start, words, unq
        flush_word()
        if words:
            stmts.append(Stmt(text=s[seg_start:end], words=words, unq="".join(unq)))
        words, unq, seg_start = [], [], next_start

    i, n = 0, len(s)
    while i < n:
        c = s[i]
        if q:
            if c == q:
                q = None
                unq.append(c)
            elif c == "\\" and q == '"' and i + 1 < n:
                word.append(s[i + 1])
                unq.append("  ")
                i += 1
            else:
                word.append(c)
                unq.append(" ")
            i += 1
            continue
        if c in "\"'":
            q, in_word = c, True
            unq.append(c)
            i += 1
            continue
        two = s[i : i + 2]
        if two in ("&&", "||", "$("):
            flush_seg(i, i + 2)
            i += 2
            continue
        prev, nxt = (s[i - 1] if i else ""), (s[i + 1] if i + 1 < n else "")
        if c in ";|`()\n" or (c == "&" and prev != ">" and nxt != ">"):
            flush_seg(i, i + 1)
            i += 1
            continue
        if c in " \t\r":
            flush_word()
            unq.append(c)
            i += 1
            continue
        word.append(c)
        unq.append(c)
        in_word = True
        i += 1
    flush_seg(n, n)

    owners = [st for st in stmts if HEREDOC.search(st.text)]
    for owner, body in zip(owners, bodies, strict=False):
        owner.body = body
    for st in stmts:
        st.assigns, st.effective, st.args = resolve_effective(st.words)
    return stmts


# ----------------------------------------------------------------------------- classification helpers
def is_pytest(st: Stmt) -> bool:
    return st.effective == "pytest" or (
        st.effective.startswith("python") and "-m" in st.args and "pytest" in st.args[st.args.index("-m") + 1 :][:1]
    )


def is_ruff_readonly(st: Stmt) -> bool:
    ruff = st.effective == "ruff" or (
        st.effective.startswith("python") and "-m" in st.args and "ruff" in st.args[st.args.index("-m") + 1 :][:1]
    )
    if not ruff:
        return False
    args = " ".join(st.args)
    if "--fix" in args or "--unsafe-fixes" in args:
        return False
    return "check" in args or "--check" in args or "--diff" in args or "--version" in args


SAFE_REPO_SCRIPT = re.compile(r"^(?:\./)?scripts/(?:validate_project\.py|security/check_secrets\.py)$")


def is_safe_repo_script(st: Stmt) -> bool:
    if not st.effective.startswith("python"):
        return False
    script = next((a for a in st.args if not a.startswith("-")), "")
    return bool(SAFE_REPO_SCRIPT.match(script.replace("\\", "/"))) and not st.has_substitution


def is_inert_for_markers(st: Stmt) -> bool:
    if st.has_substitution:
        return False
    return (
        st.effective in INERT_WORDS
        or is_pytest(st)
        or is_ruff_readonly(st)
        or is_safe_repo_script(st)
        or (st.effective == "" and not st.words)
    )


def candidate_files(st: Stmt, cwd: Path) -> list[Path]:
    """Existing, small, non-binary files named on the command line (relative to cwd or the project)."""
    out: list[Path] = []
    tokens = list(st.args)
    for i, a in enumerate(tokens):
        if a in ("-m",) and i + 1 < len(tokens) and tokens[i + 1] not in ("pytest", "ruff", "pip", "venv", "uvicorn"):
            mod = tokens[i + 1].replace(".", "/")
            tokens += [mod + ".py", mod + "/__init__.py"]
    for tok in tokens:
        if tok.startswith("-") and "=" not in tok:
            continue
        tok = tok.split("=", 1)[-1] if tok.startswith("-") else tok
        if not tok or len(tok) > 300 or ENV_FILE.search(tok):
            continue
        for base in (cwd, PROJECT_DIR, PROJECT_DIR / "backend"):
            try:
                p = Path(tok) if Path(tok).is_absolute() else base / tok
                if p.is_file() and p.suffix.lower() not in BINARY_SUFFIXES and p.stat().st_size <= MAX_SCAN_BYTES:
                    out.append(p)
                    break
            except (OSError, ValueError):
                continue
    return out


def read_text(p: Path) -> str:
    try:
        return p.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return ""


def imported_modules(source: str) -> list[str]:
    mods: list[str] = []
    for m in re.finditer(r"^\s*(?:from\s+([\w.]+)\s+import|import\s+([\w., ]+))", source, re.M):
        if m.group(1):
            mods.append(m.group(1))
        else:
            mods += [x.strip().split(" as ")[0] for x in m.group(2).split(",")]
    return [m for m in mods if m and m not in ("app.config",)]  # app.config merely names the default base URL


def file_has_markers(p: Path, cwd: Path, depth: int = 3, seen: set[Path] | None = None) -> bool:
    seen = seen if seen is not None else set()
    if p in seen:
        return False
    seen.add(p)
    text = read_text(p)
    if FILE_MARKERS.search(text):
        return True
    if depth > 0 and p.suffix == ".py":
        for mod in imported_modules(text):
            rel = mod.replace(".", "/")
            for base in (p.parent, cwd, PROJECT_DIR / "backend", PROJECT_DIR):
                for cand in (base / f"{rel}.py", base / rel / "__init__.py"):
                    if cand.is_file() and file_has_markers(cand, cwd, depth - 1, seen):
                        return True
    return False


# ----------------------------------------------------------------------------- deny rules
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


def deny_reason(cmd: str, stmts: list[Stmt]) -> str | None:
    for st in stmts:
        # Command line only: a heredoc body is usually prose or generated text, so it is handled as an ASK below.
        if ENV_FILE.search(st.text) and (ENV_READERS.match(st.effective) or re.search(r"<\s*\S*\.env\b", st.text)):
            return "reading or copying a .env file could expose the YouCam key (only the owner opens backend/.env)"
    flat = " ".join(cmd.split())
    for pattern, reason in RULES:
        if pattern.search(flat):
            return reason
    if scan_text(cmd):
        return "the command contains what looks like a secret value"
    return None


# ----------------------------------------------------------------------------- ask rules
def live_reason(cmd: str, stmts: list[Stmt], cwd: Path) -> str | None:
    """Why this command could spend YouCam units or switch to live mode, or None."""
    active = [st for st in stmts if not is_inert_for_markers(st)]
    if not active:
        return None
    # A pipe or substitution lets an "inert" statement feed an executing one, so look at everything.
    flows = bool(re.search(r"\||\$\(|`|<\(|<<<", cmd))
    haystack = cmd if flows else "\n".join(st.full for st in active)
    if LIVE_MARKERS.search(haystack):
        return "this command mentions the YouCam API host, client or probe script and can execute (may spend units)"
    if MODE_MARKERS.search(MODE_MOCK_OK.sub("", haystack)):
        return "this command touches YouCam mode/env-file settings and could switch the backend to live mode"
    for st in active:
        if st.effective in ("source", ".") and any(re.search(r"env", a, re.I) for a in st.args):
            return "this sources an env file, which could switch the backend to live mode"
        if EXEC_WORDS.match(st.effective) or st.effective in ("python", "py"):
            for f in candidate_files(st, cwd):
                if file_has_markers(f, cwd):
                    return f"this runs or reads {f.name}, which contains YouCam API code (may spend units)"
    return None


def guardrail_reason(stmts: list[Stmt], cwd: Path) -> str | None:
    """Why this command could modify a guardrail file, or None."""
    if not PROTECTED_PATH_PATTERNS:
        return None
    for st in stmts:
        if is_pytest(st) or is_ruff_readonly(st) or is_safe_repo_script(st):
            continue
        text = st.full
        hit = any(p.search(text) for p in PROTECTED_PATH_PATTERNS)
        if hit:
            if st.effective == "git":
                sub = st.git_sub
                if sub not in GIT_MODIFYING and not re.search(r"hooksPath", text, re.I):
                    continue
            elif st.effective in READONLY_WORDS and not st.redirects:
                continue
            return "this command could modify a guardrail file (hooks, settings, git hooks, scanner, CI or .gitignore)"
        # Indirect: patches and scripts whose CONTENT targets guardrail files.
        patching = st.effective == "patch" or (st.effective == "git" and st.git_sub in ("apply", "am"))
        if patching or EXEC_WORDS.match(st.effective):
            for f in candidate_files(st, cwd):
                body = read_text(f)
                if any(p.search(body) for p in PROTECTED_PATH_PATTERNS):
                    return f"{f.name} targets guardrail files and this command would run or apply it"
    return None


def env_body_reason(stmts: list[Stmt]) -> str | None:
    """An interpreter fed a heredoc that names an env file might read it; let the owner decide."""
    for st in stmts:
        if st.body and ENV_FILE.search(st.body) and EXEC_WORDS.match(st.effective):
            return "a script passed to this command mentions an env file; approve only if it does not read it"
    return None


def decide(cmd: str, cwd: Path) -> tuple[str, str]:
    stmts = tokenize(cmd)
    reason = deny_reason(cmd, stmts)
    if reason:
        return "deny", reason
    reason = env_body_reason(stmts)
    if reason:
        return "ask", reason
    if DEGRADED and any(not is_inert_for_markers(st) for st in stmts):
        return "ask", "the guard's shared pattern module is unavailable, so this command can't be checked"
    reason = live_reason(cmd, stmts, cwd)
    if reason:
        return "ask", reason + ". Approve only if you asked for this specific live call."
    reason = guardrail_reason(stmts, cwd)
    if reason:
        return "ask", reason
    return "allow", ""


# ----------------------------------------------------------------------------- hook protocol
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


def main() -> None:
    try:
        data = json.loads(sys.stdin.read())
    except Exception:
        ask("the hook input could not be parsed, so this command can't be checked")
    try:
        tool_input = data.get("tool_input") if isinstance(data, dict) else None
        if not isinstance(tool_input, dict):
            ask("the hook input had an unexpected shape, so this command can't be checked")
        cmd = tool_input.get("command")
        if cmd is None:
            sys.exit(0)  # a tool call without a command (nothing to execute)
        if not isinstance(cmd, str):
            ask("the command had an unexpected type, so it can't be checked")
        cwd = Path(str(data.get("cwd") or os.getcwd()))
        verdict, reason = decide(cmd, cwd)
    except Exception as exc:  # never fail open
        ask(f"the guard hit an internal error ({type(exc).__name__}); treating this command as needing approval")
    if verdict == "deny":
        block(reason)
    if verdict == "ask":
        ask(reason)
    sys.exit(0)


if __name__ == "__main__":
    main()
