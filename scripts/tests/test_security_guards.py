"""Tests for the deterministic guardrails: secret patterns, Claude Code hooks, pre-commit scanner.

Fake secrets are assembled at runtime so this file never contains a literal secret-shaped string.
Run: python -m pytest scripts/tests -q

Hook decisions are asserted precisely:
  "deny"  -> exit code 2 (reason on stderr)
  "ask"   -> exit code 0 + JSON hookSpecificOutput.permissionDecision == "ask" (owner gets a permission prompt)
  "allow" -> exit code 0 and no decision output
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
HOST = "yce-api-01." + "makeupar.com"


def run_hook(script: str, payload: dict) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(ROOT / ".claude" / "hooks" / script)],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        env={"CLAUDE_PROJECT_DIR": str(ROOT), "PATH": "", "SYSTEMROOT": "C:\\Windows"},
    )


def decision(proc: subprocess.CompletedProcess) -> str:
    if proc.returncode == 2:
        return "deny"
    assert proc.returncode == 0, f"hook crashed (rc={proc.returncode}): {proc.stderr}"
    out = proc.stdout.strip()
    if not out:
        return "allow"
    payload = json.loads(out)["hookSpecificOutput"]
    assert payload["hookEventName"] == "PreToolUse"
    assert payload["permissionDecisionReason"].startswith("GlowCue guard:")
    return payload["permissionDecision"]


def bash(cmd: str, cwd: Path = ROOT) -> str:
    return decision(run_hook("guard_bash.py", {"tool_name": "Bash", "cwd": str(cwd), "tool_input": {"command": cmd}}))


def edit(file_path: str, **fields) -> str:
    return decision(
        run_hook("guard_edits.py", {"tool_name": "Write", "tool_input": {"file_path": file_path, **fields}})
    )


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


# ---------- guard_bash.py: DENY ----------
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
        f"echo {FAKE_KEY}",
        # deny beats ask: a live call that also leaks the env file is denied outright
        f"cat backend/.env && curl https://{HOST}/s2s/v1.0/client/credit",
    ],
)
def test_bash_guard_denies(cmd):
    assert bash(cmd) == "deny", cmd


# ---------- guard_bash.py: ASK (live YouCam calls need a real human prompt) ----------
@pytest.mark.parametrize(
    "cmd",
    [
        f"echo ok; curl -s https://{HOST}/s2s/v2.0/credit/feature-cost",
        f"curl -H 'Authorization: Bearer x' https://{HOST}/s2s/v1.0/client/credit",
        f"Invoke-RestMethod -Uri https://{HOST}/s2s/v1.0/client/credit",
        "python backend/scripts/probe_youcam.py selfie.jpg",
        "backend/.venv/Scripts/python backend/scripts/probe_youcam.py selfie.jpg",
        "./backend/scripts/probe_youcam.py selfie.jpg",
        "YOUCAM_MODE=live uvicorn app.main:app",
        "export YOUCAM_MODE=live && uvicorn app.main:app",
        "$env:YOUCAM_MODE='live'; uvicorn app.main:app",
        f"python -c \"import httpx; httpx.get('https://{HOST}/s2s/v1.0/client/credit')\"",
        # REGRESSION (High finding #1): the old self-approval token must NOT bypass the prompt
        "GLOWCUE_LIVE_APPROVED=1 python backend/scripts/probe_youcam.py selfie.jpg",
        f"GLOWCUE_LIVE_APPROVED=1 curl https://{HOST}/s2s/v1.0/client/credit",
        "GLOWCUE_LIVE_APPROVED=1 YOUCAM_MODE=live uvicorn app.main:app",
    ],
)
def test_bash_guard_asks_owner_for_live_calls(cmd):
    assert bash(cmd) == "ask", cmd


def test_no_variable_or_token_can_self_approve():
    """Whatever the agent prefixes, a live call still requires the owner's prompt."""
    for prefix in ["", "GLOWCUE_LIVE_APPROVED=1 ", "APPROVED=yes ", "OWNER_OK=1 ", "CLAUDE_APPROVED=true "]:
        assert bash(f"{prefix}python backend/scripts/probe_youcam.py x.jpg") == "ask", prefix


def test_script_containing_youcam_code_asks(tmp_path):
    sneaky = tmp_path / "harmless_name.py"
    sneaky.write_text(f"import httpx\nhttpx.get('https://{HOST}/s2s/v1.0/client/credit')\n", encoding="utf-8")
    assert bash(f"python {sneaky}") == "ask"
    client_user = tmp_path / "use_client.py"
    client_user.write_text("from app.services.youcam_client import YouCamClient\n", encoding="utf-8")
    assert bash("python use_client.py", cwd=tmp_path) == "ask"


def test_plain_script_and_tests_do_not_ask(tmp_path):
    plain = tmp_path / "plain.py"
    plain.write_text("print('hello')\n", encoding="utf-8")
    assert bash(f"python {plain}") == "allow"
    mocked_test = tmp_path / "test_youcam_client.py"
    mocked_test.write_text(f"BASE = 'https://{HOST}'  # used only with httpx.MockTransport\n", encoding="utf-8")
    assert bash(f"python -m pytest {mocked_test} -q") == "allow"


@pytest.mark.parametrize(
    "cmd",
    [
        "sed -i 's/ask/allow/' .claude/hooks/guard_bash.py",
        "echo '{}' > .claude/settings.json",
        "rm .githooks/pre-commit",
        "cp /tmp/x.py scripts/security/secret_patterns.py",
        "git checkout HEAD~1 -- .claude/hooks/guard_edits.py",
    ],
)
def test_bash_guard_asks_before_modifying_guardrails(cmd):
    assert bash(cmd) == "ask", cmd


# ---------- guard_bash.py: ALLOW ----------
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
        "uvicorn app.main:app --reload",  # mode comes from backend/.env, which only the owner edits
        "cat .claude/hooks/guard_bash.py",  # reading guardrails is fine
        "git diff .claude/settings.json",
        # regression (31 Oct): prose in commit messages must not trigger the .env or live-call rules
        "git commit -q -F - <<'EOF'\nchore: init\n\nAdd ignore rules (secrets, .env files, photos)\nEOF",
        'git commit -m "feat(youcam): add probe_youcam script and docs for yce-api host"',
        "python -m pytest backend/tests -q -k app.main",
    ],
)
def test_bash_guard_allows(cmd):
    assert bash(cmd) == "allow", cmd


# ---------- guard_edits.py ----------
def test_edit_guard_denies_env_and_secrets():
    assert edit("C:/x/backend/.env", content="A=1") == "deny"
    assert edit("app/config.py", content=f"KEY='{FAKE_KEY}'") == "deny"
    assert (
        decision(run_hook("guard_edits.py", {"tool_input": {"file_path": "x.py", "edits": [{"new_string": FAKE_RSA}]}}))
        == "deny"
    )
    # deny beats ask: a secret written into a guardrail file is still denied
    assert edit(".claude/hooks/guard_bash.py", content=f"K='{FAKE_KEY}'") == "deny"


@pytest.mark.parametrize(
    "path",
    [
        "C:/Users/USER/glowcue/.claude/hooks/guard_bash.py",
        ".claude/hooks/guard_edits.py",
        ".claude/settings.json",
        ".claude/settings.local.json",
        ".githooks/pre-commit",
        "scripts/security/secret_patterns.py",
    ],
)
def test_edit_guard_asks_owner_for_guardrail_files(path):
    assert edit(path, content="# change") == "ask", path


def test_edit_guard_allows_normal_code_and_example():
    assert edit("backend/.env.example", content="YOUCAM_API_KEY=your_api_key_here") == "allow"
    assert edit("app/main.py", new_string="app = FastAPI()") == "allow"
    assert edit(".claude/skills/x/SKILL.md", content="# skill") == "allow"
    assert edit("scripts/tests/test_x.py", content="def test_x(): pass") == "allow"
