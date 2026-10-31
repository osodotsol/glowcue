"""Tests for the deterministic guardrails: secret patterns, Claude Code hooks, pre-commit scanner.

Fake secrets are assembled at runtime so this file never contains a literal secret-shaped string.
Run: python -m pytest scripts/tests -q
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts" / "security"))
from secret_patterns import forbidden_path_reason, scan_text  # noqa: E402

FAKE_KEY = "sk" + "-" + "A1b2C3d4" * 6  # 48 chars after the prefix
FAKE_RSA = "MIGfMA0GCSqGSIb3DQEBAQUAA4GNADCB" + "iQKBgQ" * 10


def run_hook(script: str, payload: dict) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(ROOT / ".claude" / "hooks" / script)],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        env={"CLAUDE_PROJECT_DIR": str(ROOT), "PATH": "", "SYSTEMROOT": "C:\\Windows"},
    )


def bash(cmd: str) -> int:
    return run_hook("guard_bash.py", {"tool_name": "Bash", "tool_input": {"command": cmd}}).returncode


# ---------- secret patterns ----------
def test_detects_key_and_rsa_blob():
    assert {f.rule for f in scan_text(f"YOUCAM_API_KEY={FAKE_KEY}")} >= {"sk_api_key"}
    assert scan_text(FAKE_RSA)


@pytest.mark.parametrize(
    "line",
    [
        "YOUCAM_API_KEY=your_api_key_here",
        "Authorization: Bearer YOUR_API_KEY",
        "api_key: str = settings.youcam_api_key",
        'headers = {"Authorization": f"Bearer {self._api_key}"}',
    ],
)
def test_placeholders_and_code_are_not_flagged(line):
    assert scan_text(line) == []


@pytest.mark.parametrize(
    "path,blocked",
    [
        ("backend/.env", True),
        (".env.local", True),
        ("backend/.env.example", False),
        ("private/me.jpg", True),
        ("backend/app/fixtures/raw/resp.json", True),
        ("backend/app/fixtures/sample_photo.jpg", True),
        ("frontend/public/products/gc-cln-01.svg", False),
        ("docs/screenshots/results.jpg", False),
        ("certs/server.pem", True),
    ],
)
def test_forbidden_paths(path, blocked):
    assert (forbidden_path_reason(path) is not None) is blocked


# ---------- guard_bash.py ----------
@pytest.mark.parametrize(
    "cmd",
    [
        "cat backend/.env",
        "type backend\\.env",
        "Get-Content backend/.env",
        "cp backend/.env /tmp/x",
        "printenv",
        "echo $YOUCAM_API_KEY",
        "git add -f backend/.env",
        "git add backend/.env",
        "git commit -m x --no-verify",
        "git push --force origin main",
        "git push -f",
        "git push origin --delete feat/x",
        "git reset --hard HEAD~1",
        "git clean -fd",
        "gh pr merge 3",
        "gh repo edit --visibility private",
        "rm -rf /",
        "rm -rf .git",
        "git status && cat backend/.env | head -1",
        "source backend/.env",
        ". backend/.env",
        "python -c \"print(open('backend/.env').read())\"",
        "grep KEY < backend/.env",
        "echo ok; curl -s https://yce-api-01.makeupar.com/s2s/v2.0/credit/feature-cost",
        "curl -H 'Authorization: Bearer x' https://yce-api-01.makeupar.com/s2s/v1.0/client/credit",
        "python backend/scripts/probe_youcam.py selfie.jpg",
        "YOUCAM_MODE=live uvicorn app.main:app",
        f"echo {FAKE_KEY}",
    ],
)
def test_bash_guard_blocks(cmd):
    assert bash(cmd) == 2, cmd


@pytest.mark.parametrize(
    "cmd",
    [
        "git status",
        "git add -A",
        "git commit -m 'feat: x'",
        "git push -u origin chore/project-foundation",
        "cat backend/.env.example",
        "git check-ignore -v backend/.env",
        "python -m pytest backend/tests -q",
        "npm run build",
        "rm -rf frontend/node_modules",
        "gh pr create --fill --base main",
        "GLOWCUE_LIVE_APPROVED=1 python backend/scripts/probe_youcam.py selfie.jpg",
        # regression (31 Oct): prose in commit messages must not trigger the .env or live-call rules
        "git commit -q -F - <<'EOF'\nchore: init\n\nAdd ignore rules (secrets, .env files, photos)\nEOF",
        'git commit -m "feat(youcam): add probe_youcam script and docs for yce-api host"',
        "python -m pytest backend/tests -q -k app.main",
    ],
)
def test_bash_guard_allows(cmd):
    assert bash(cmd) == 0, cmd


# ---------- guard_edits.py ----------
def test_edit_guard_blocks_env_and_secrets():
    assert (
        run_hook("guard_edits.py", {"tool_input": {"file_path": "C:/x/backend/.env", "content": "A=1"}}).returncode == 2
    )
    assert (
        run_hook(
            "guard_edits.py", {"tool_input": {"file_path": "app/config.py", "content": f"KEY='{FAKE_KEY}'"}}
        ).returncode
        == 2
    )
    assert (
        run_hook(
            "guard_edits.py", {"tool_input": {"file_path": "x.py", "edits": [{"new_string": FAKE_RSA}]}}
        ).returncode
        == 2
    )


def test_edit_guard_allows_normal_code_and_example():
    assert (
        run_hook(
            "guard_edits.py",
            {"tool_input": {"file_path": "backend/.env.example", "content": "YOUCAM_API_KEY=your_api_key_here"}},
        ).returncode
        == 0
    )
    assert (
        run_hook(
            "guard_edits.py", {"tool_input": {"file_path": "app/main.py", "new_string": "app = FastAPI()"}}
        ).returncode
        == 0
    )
