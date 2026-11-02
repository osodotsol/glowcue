"""Scan the repository for secrets and forbidden files.

Usage:
  python scripts/security/check_secrets.py --staged    # pre-commit hook: staged content only
  python scripts/security/check_secrets.py --all       # CI: every tracked file
  python scripts/security/check_secrets.py --history   # audit: every commit's added lines

Exit code 1 when anything is found. Output never prints a full secret (values are redacted).
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from secret_patterns import forbidden_path_reason, scan_text  # noqa: E402

BINARY_SUFFIXES = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".ico", ".woff", ".woff2", ".zip", ".pdf"}
SKIP_FILES = {"scripts/security/secret_patterns.py", "scripts/tests/test_security_guards.py"}


def git(*args: str) -> str:
    return subprocess.run(
        ["git", *args], capture_output=True, text=True, encoding="utf-8", errors="replace", check=True
    ).stdout


def main() -> int:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--staged", action="store_true")
    mode.add_argument("--all", action="store_true")
    mode.add_argument("--history", action="store_true")
    args = parser.parse_args()
    photo_ok = os.environ.get("GLOWCUE_PHOTO_APPROVED") == "1"
    problems: list[str] = []

    if args.history:
        log = git("log", "--all", "-p", "--no-color", "--unified=0")
        current = "?"
        for line in log.splitlines():
            if line.startswith("+++ b/"):
                current = line[6:]
            elif line.startswith("+") and not line.startswith("+++") and current not in SKIP_FILES:
                for f in scan_text(line[1:]):
                    problems.append(f"history:{current}: {f.rule} {f.excerpt}")
    else:
        if args.staged:
            files = [f for f in git("diff", "--cached", "--name-only", "--diff-filter=ACMR").splitlines() if f]
        else:
            files = [f for f in git("ls-files").splitlines() if f]
        for path in files:
            reason = forbidden_path_reason(path, photo_approved=photo_ok)
            if reason:
                problems.append(f"{path}: {reason}")
                continue
            if path in SKIP_FILES or Path(path).suffix.lower() in BINARY_SUFFIXES:
                continue
            try:
                text = (
                    git("show", f":{path}") if args.staged else Path(path).read_text(encoding="utf-8", errors="replace")
                )
            except (subprocess.CalledProcessError, OSError):
                continue
            for f in scan_text(text):
                problems.append(f"{path}:{f.line}: {f.rule} {f.excerpt}")

    if problems:
        print("SECRET SCAN FAILED — remove these before committing:", file=sys.stderr)
        for p in problems:
            print(f"  - {p}", file=sys.stderr)
        print(
            "If a real key was committed, rotate it in the YouCam console; rewriting history is not enough.",
            file=sys.stderr,
        )
        return 1
    print(f"secret scan OK ({'staged' if args.staged else 'history' if args.history else 'all tracked files'})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
