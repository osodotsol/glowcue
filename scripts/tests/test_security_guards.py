"""Tests for the deterministic guardrails: secret patterns, Claude Code hooks, settings wiring, pre-commit scanner.

Fake secrets are assembled at runtime so this file never contains a literal secret-shaped string.
Run: python -m pytest scripts/tests -q

Hook decisions are asserted precisely:
  "deny"  -> exit code 2 (reason on stderr)
  "ask"   -> exit code 0 + JSON hookSpecificOutput.permissionDecision == "ask" (the OWNER gets a permission prompt)
  "allow" -> exit code 0 and no decision output

Most cases call `decide()` in-process for speed; a representative subset runs the hook as a separate process to
verify the real stdin/stdout/exit-code protocol. Every bypass found in the PR #1 adversarial review
(commit b5a4362) has a regression test below (search for "REVIEW").
"""

from __future__ import annotations

import importlib.util
import io
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
os.environ["CLAUDE_PROJECT_DIR"] = str(ROOT)
sys.path.insert(0, str(ROOT / "scripts" / "security"))
from secret_patterns import forbidden_path_reason, protected_path_match, scan_text  # noqa: E402


def load_hook(name: str):
    spec = importlib.util.spec_from_file_location(f"hook_{name}", ROOT / ".claude" / "hooks" / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module  # dataclasses look the defining module up here
    spec.loader.exec_module(module)
    return module


GB = load_hook("guard_bash")
GE = load_hook("guard_edits")

FAKE_KEY = "sk" + "-" + "A1b2C3d4" * 6  # 48 chars after the prefix
FAKE_RSA = "MIGfMA0GCSqGSIb3DQEBAQUAA4GNADCB" + "iQKBgQ" * 10
HOST = "yce-api-01." + "makeupar.com"
URL = f"https://{HOST}/s2s/v1.0/client/credit"


# ----------------------------------------------------------------------------- helpers
def run_hook(script: str, payload, raw: str | None = None, project_dir: Path = ROOT) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(ROOT / ".claude" / "hooks" / script)],
        input=raw if raw is not None else json.dumps(payload),
        capture_output=True,
        text=True,
        env={"CLAUDE_PROJECT_DIR": str(project_dir), "PATH": "", "SYSTEMROOT": "C:\\Windows"},
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
    """In-process decision for a shell command."""
    return GB.decide(cmd, cwd)[0]


def bash_proc(cmd: str, cwd: Path = ROOT) -> str:
    """Decision through the real hook process protocol."""
    return decision(run_hook("guard_bash.py", {"tool_name": "Bash", "cwd": str(cwd), "tool_input": {"command": cmd}}))


def edit(file_path: str, **fields) -> str:
    return GE.decide({"file_path": file_path, **fields})[0]


def edit_proc(file_path: str, **fields) -> str:
    return decision(
        run_hook("guard_edits.py", {"tool_name": "Write", "tool_input": {"file_path": file_path, **fields}})
    )


def write_files(base: Path, files: dict[str, str]) -> None:
    for rel, content in files.items():
        target = base / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")


# ----------------------------------------------------------------------------- secret patterns
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


@pytest.mark.parametrize(
    "path,protected",
    [
        (".claude/hooks/guard_bash.py", True),
        ("C:/Users/USER/glowcue/.claude/hooks/guard_edits.py", True),
        (".claude\\settings.json", True),
        (".claude/settings.local.json", True),
        ("~/.claude/settings.json", True),
        (".githooks/pre-commit", True),
        ("scripts/security/secret_patterns.py", True),
        ("scripts/tests/test_security_guards.py", True),
        ("scripts/validate_project.py", True),
        (".github/workflows/ci.yml", True),
        (".gitignore", True),
        ("git config core.hooksPath /dev/null", True),
        (".Claude/Hooks/guard_bash.py", True),
        (".claude/skills/x/SKILL.md", False),
        (".claude/rules/security.md", False),
        (".claude/agents/pr-reviewer.md", False),
        ("backend/app/main.py", False),
        ("frontend/src/App.tsx", False),
        ("docs/SECURITY_PRIVACY.md", False),
        ("README.md", False),
        ("backend/.env.example", False),
    ],
)
def test_protected_path_list(path, protected):
    assert protected_path_match(path) is protected, path


# ----------------------------------------------------------------------------- guard_bash: DENY
DENY_CASES = [
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
    "timeout 5 cat backend/.env",
    "bash -c 'cat backend/.env'",
    "xargs cat < backend/.env",
    f"echo {FAKE_KEY}",
    # deny beats ask: a live call that also leaks the env file is denied outright
    f"cat backend/.env && curl {URL}",
]


@pytest.mark.parametrize("cmd", DENY_CASES)
def test_bash_guard_denies(cmd):
    assert bash(cmd) == "deny", cmd


def test_heredoc_prose_mentioning_an_env_file_asks_instead_of_denying():
    """Regression: a script body that merely mentions .env is the owner's call, not a deny."""
    cmd = "python -I - <<'EOF'\nprint('Configure backend/.env and the .env file as described')\nEOF"
    assert bash(cmd) == "ask"
    assert bash("cat <<'EOF'\nthe .env file holds the key\nEOF") == "allow"  # a plain cat of prose is harmless
    assert bash("git commit -q -F - <<'EOF'\nfix: protect .env files\nEOF") == "allow"
    # ...while an actual read on the command line is still a hard deny
    assert bash("python -c \"print(open('backend/.env').read())\"") == "deny"


def test_deny_cannot_be_downgraded_by_adding_ask_triggers():
    """Hard-deny rules win even when the same command would also merely 'ask'."""
    for cmd in (f"cat backend/.env; curl {URL}", "git push --force; python backend/scripts/probe_youcam.py"):
        assert bash(cmd) == "deny", cmd


# ----------------------------------------------------------------------------- guard_bash: ASK (live YouCam calls)
@pytest.mark.parametrize(
    "cmd",
    [
        f"echo ok; curl -s {URL}",
        f"curl -H 'Authorization: Bearer x' {URL}",
        f"Invoke-RestMethod -Uri {URL}",
        "python backend/scripts/probe_youcam.py selfie.jpg",
        "backend/.venv/Scripts/python backend/scripts/probe_youcam.py selfie.jpg",
        "./backend/scripts/probe_youcam.py selfie.jpg",
        "YOUCAM_MODE=live uvicorn app.main:app",
        "export YOUCAM_MODE=live && uvicorn app.main:app",
        "$env:YOUCAM_MODE='live'; uvicorn app.main:app",
        f"python -c \"import httpx; httpx.get('{URL}')\"",
        # the old self-approval token must NOT bypass the prompt
        "GLOWCUE_LIVE_APPROVED=1 python backend/scripts/probe_youcam.py selfie.jpg",
        f"GLOWCUE_LIVE_APPROVED=1 curl {URL}",
        "GLOWCUE_LIVE_APPROVED=1 YOUCAM_MODE=live uvicorn app.main:app",
    ],
)
def test_bash_guard_asks_owner_for_live_calls(cmd):
    assert bash(cmd) == "ask", cmd
    assert bash_proc(cmd) == "ask", cmd  # and through the real hook protocol


def test_no_variable_or_token_can_self_approve():
    """Whatever the agent prefixes, a live call still requires the owner's prompt."""
    prefixes = [
        "",
        "GLOWCUE_LIVE_APPROVED=1 ",
        "APPROVED=yes ",
        "OWNER_OK=1 ",
        "CLAUDE_APPROVED=true ",
        "export OK=1; ",
    ]
    for prefix in prefixes:
        assert bash(f"{prefix}python backend/scripts/probe_youcam.py x.jpg") == "ask", prefix


def test_old_token_mechanism_is_gone_from_the_guards():
    for name in ("guard_bash.py", "guard_edits.py"):
        source = (ROOT / ".claude" / "hooks" / name).read_text(encoding="utf-8")
        assert "LIVE_TOKEN" not in source, name
        assert "LIVE_APPROVED" not in source, name
        assert "approved =" not in source, name


# REVIEW H1: shell and process wrappers (every route reported in the b5a4362 review)
WRAPPED_CALL = f"curl {URL}"
WRAPPERS = [
    'bash -c "{c}"',
    "sh -c '{c}'",
    'powershell -Command "{c}"',
    'pwsh -NoProfile -Command "{c}"',
    "cmd /c {c}",
    "timeout 10 {c}",
    "nice {c}",
    "nice -n 5 {c}",
    "command {c}",
    "env FOO=1 {c}",
    "nohup {c}",
    "time {c}",
    "stdbuf -oL {c}",
    "sudo {c}",
    "eval '{c}'",
    "( {c} )",
    "echo start && {c}",
    "echo start; {c}",
    "false || {c}",
    "{c} | cat",
    "echo $({c})",
    "echo `{c}`",
    f"echo {URL} | xargs curl",
    f"echo {URL} | xargs -I{{}} sh -c 'curl {{}}'",
]


@pytest.mark.parametrize("template", WRAPPERS)
def test_REVIEW_H1_wrappers_cannot_hide_a_live_call(template):
    cmd = template.format(c=WRAPPED_CALL) if "{c}" in template else template
    assert bash(cmd) == "ask", cmd


def test_REVIEW_H1_uv_run_and_other_runners():
    for cmd in (
        "uv run backend/scripts/probe_youcam.py x.jpg",
        "uvx --from httpx python probe_youcam.py",
        "poetry run python backend/scripts/probe_youcam.py",
        "npx ts-node probe_youcam.ts",
        "pipx run probe_youcam",
    ):
        assert bash(cmd) == "ask", cmd


def test_REVIEW_H1_python_c_with_settings_driven_call():
    cmd = (
        'python -c "from app.config import Settings; import httpx; s = Settings(); '
        "httpx.get(s.youcam_base_url + '/s2s/v1.0/client/credit')\""
    )
    assert bash(cmd) == "ask"


def test_REVIEW_H1_host_built_at_runtime_still_has_a_marker():
    cmd = "python -c \"import httpx; h = 'yce-api-01.make' + 'upar.com'; httpx.get('https://' + h)\""
    assert bash(cmd) == "ask"


# REVIEW M1: calls that take their target from files the command executes or reads
def test_REVIEW_M1_python_module_resolved_to_a_file(tmp_path):
    write_files(tmp_path, {"scripts/some_probe.py": f"import httpx\nhttpx.get('{URL}')\n"})
    assert bash("python -m scripts.some_probe", tmp_path) == "ask"


def test_REVIEW_M1_node_script_and_curl_config(tmp_path):
    write_files(tmp_path, {"live.js": f"fetch('{URL}')\n", "req.txt": f'url = "{URL}"\n'})
    assert bash("node live.js", tmp_path) == "ask"
    assert bash("curl -K req.txt", tmp_path) == "ask"
    assert bash("curl --config=req.txt", tmp_path) == "ask"


def test_REVIEW_M1_script_using_settings_without_literal_host(tmp_path):
    write_files(
        tmp_path,
        {"innocent.py": "from app.config import Settings\nimport httpx\nhttpx.get(Settings().youcam_base_url)\n"},
    )
    assert bash("python innocent.py", tmp_path) == "ask"


def test_REVIEW_M1_script_importing_a_helper_that_holds_the_host(tmp_path):
    write_files(
        tmp_path,
        {"outer.py": "import helper\nhelper.go()\n", "helper.py": f"import httpx\ndef go():\n    httpx.get('{URL}')\n"},
    )
    assert bash("python outer.py", tmp_path) == "ask"


def test_script_with_literal_host_asks_and_plain_script_does_not(tmp_path):
    write_files(tmp_path, {"direct.py": f"import httpx\nhttpx.get('{URL}')\n", "plain.py": "print('hello')\n"})
    assert bash("python direct.py", tmp_path) == "ask"
    assert bash("python plain.py", tmp_path) == "allow"


def test_script_that_imports_app_config_only_is_not_flagged(tmp_path):
    write_files(tmp_path, {"uses_cfg.py": "from app.config import get_settings\nprint(get_settings().currency)\n"})
    assert bash("python uses_cfg.py", tmp_path) == "allow"


# REVIEW M2: switching to live mode without the literal YOUCAM_MODE=live
@pytest.mark.parametrize(
    "cmd",
    [
        "uvicorn app.main:app --env-file live.env",
        "set -a; source live.env; uvicorn app.main:app",
        ". ./prod.env && uvicorn app.main:app",
        "export YOUCAM_MODE=$(echo bGl2ZQ== | base64 -d) && uvicorn app.main:app",
        "[Environment]::SetEnvironmentVariable('YOUCAM_MODE','live'); uvicorn app.main:app",
        "LIVE_ANALYSIS_ENABLED=true uvicorn app.main:app",
        "python -m dotenv run -- uvicorn app.main:app",
    ],
)
def test_REVIEW_M2_mode_switching_routes_ask(cmd):
    assert bash(cmd) == "ask", cmd


def test_explicit_mock_mode_commands_are_allowed():
    assert bash("YOUCAM_MODE=mock uvicorn app.main:app --reload") == "allow"
    assert bash("YOUCAM_MODE=mock python -m pytest backend/tests -q") == "allow"


# ----------------------------------------------------------------------------- guard_bash: ASK (guardrail files)
@pytest.mark.parametrize(
    "cmd",
    [
        "sed -i 's/ask/allow/' .claude/hooks/guard_bash.py",
        "echo '{}' > .claude/settings.json",
        "echo x >> .gitignore",
        "rm .githooks/pre-commit",
        "rm -rf .claude",
        "cp /tmp/x.py scripts/security/secret_patterns.py",
        "mv /tmp/x scripts/validate_project.py",
        "git checkout HEAD~1 -- .claude/hooks/guard_edits.py",
        "git restore .claude/settings.json",
        "git stash -- .githooks",
        "cat evil.py | tee scripts/security/check_secrets.py",
        "truncate -s 0 .github/workflows/ci.yml",
        "git config core.hooksPath /dev/null",
        "git -c core.hooksPath=/dev/null commit -m x",
        "Set-Content .claude/settings.json '{}'",
        "Remove-Item .claude/hooks/guard_bash.py",
        # REVIEW H3: interpreter writes
        "python -c \"open('.claude/settings.json','w').write('{}')\"",
        "python3 -c \"import pathlib; pathlib.Path('.githooks/pre-commit').unlink()\"",
        "node -e \"require('fs').writeFileSync('.claude/hooks/guard_bash.py','')\"",
        "perl -pi -e 's/ask/allow/' .claude/hooks/guard_bash.py",
        "bash -c 'echo x > .claude/settings.json'",
        "powershell -Command \"Set-Content .claude/settings.json '{}'\"",
        "timeout 5 sed -i 's/a/b/' .claude/hooks/guard_bash.py",
        "echo hi | xargs -I{} sh -c 'echo {} > .claude/settings.json'",
    ],
)
def test_bash_guard_asks_before_modifying_guardrails(cmd):
    assert bash(cmd) == "ask", cmd


def test_REVIEW_H3_git_apply_and_patch_with_a_patch_naming_guardrails(tmp_path):
    patch = '--- a/.claude/settings.json\n+++ b/.claude/settings.json\n@@ -1 +1 @@\n-{}\n+{"hooks": {}}\n'
    write_files(
        tmp_path, {"weaken.patch": patch, "harmless.patch": "--- a/README.md\n+++ b/README.md\n@@ -1 +1 @@\n-a\n+b\n"}
    )
    assert bash("git apply weaken.patch", tmp_path) == "ask"
    assert bash("git am weaken.patch", tmp_path) == "ask"
    assert bash("patch -p1 < weaken.patch", tmp_path) == "ask"
    assert bash("git apply harmless.patch", tmp_path) == "allow"


def test_REVIEW_H3_script_file_that_edits_guardrails(tmp_path):
    write_files(tmp_path, {"sneaky.py": "open('.claude/settings.json', 'w').write('{}')\n"})
    assert bash("python sneaky.py", tmp_path) == "ask"
    write_files(tmp_path, {"sneaky.sh": "echo '{}' > .githooks/pre-commit\n"})
    assert bash("bash sneaky.sh", tmp_path) == "ask"


# ----------------------------------------------------------------------------- guard_bash: ALLOW
@pytest.mark.parametrize(
    "cmd",
    [
        "git status",
        "git add -A",
        "git add .claude/hooks/guard_bash.py scripts/security/secret_patterns.py",
        "git commit -m 'feat: x'",
        "git push -u origin chore/project-foundation",
        "cat backend/.env.example",
        "git check-ignore -v backend/.env",
        "python -m pytest backend/tests -q",
        "python -m pytest scripts/tests/test_security_guards.py -q",
        "backend/.venv/Scripts/python -m pytest backend/tests scripts/tests -q",
        "python scripts/validate_project.py",
        "python scripts/security/check_secrets.py --all",
        "python -I scripts/security/check_secrets.py --history",
        "backend/.venv/Scripts/python -m ruff check backend scripts .claude/hooks",
        "backend/.venv/Scripts/python -m ruff format --check scripts .claude/hooks",
        "npm run build",
        "rm -rf frontend/node_modules",
        "gh pr create --fill --base main",
        "uvicorn app.main:app --reload",  # mode comes from backend/.env, which only the owner edits
        "cat .claude/hooks/guard_bash.py",  # reading guardrails is fine
        "grep -n ask .claude/settings.json",
        "ls .claude/hooks",
        "head -20 scripts/security/secret_patterns.py",
        "git diff .claude/settings.json",
        "git log --oneline -- .githooks",
        "git show HEAD:.claude/settings.json",
        "cat docs/YOUCAM_API.md",
        f"grep -rn {HOST} docs",
        "git grep -n yce-api -- docs",
        "echo hello > notes.txt",
        # regressions: prose that merely mentions markers/paths must not prompt
        "git commit -q -F - <<'EOF'\nchore: init\n\nAdd ignore rules (secrets, .env files, photos)\nEOF",
        f'git commit -m "docs: the API host is {HOST}"',
        'git commit -m "feat(youcam): add probe_youcam script"',
        f"git commit -q -F - <<'EOF'\nfix: the {HOST} host\n\nMentions .claude/settings.json, probe_youcam.\nEOF",
        f"gh pr create --title 'x' --body 'Mentions {HOST} and probe_youcam'",
        "python -m pytest backend/tests -q -k app.main",
    ],
)
def test_bash_guard_allows(cmd):
    assert bash(cmd) == "allow", cmd


def test_pytest_is_exempt_from_the_prompt_by_design_because_tests_are_network_isolated(tmp_path):
    """Documented limitation (PR #1 review): a test file with a real call is not prompted for; backend/tests/conftest.py
    blocks all outbound traffic instead (see backend/tests/test_network_isolation.py)."""
    write_files(tmp_path, {"test_live.py": f"import httpx\ndef test_x():\n    httpx.get('{URL}')\n"})
    assert bash("python -m pytest test_live.py -q", tmp_path) == "allow"


# ----------------------------------------------------------------------------- documented limitations (strict xfail)
@pytest.mark.xfail(strict=True, reason="KNOWN LIMITATION: a host assembled from fragments has no marker in the text")
def test_KNOWN_LIMIT_fully_fragmented_host_is_not_detected():
    cmd = "python -c \"import httpx; h = 'yce' + '-ap' + 'i-01.makeu' + 'par.com'; httpx.get('https://' + h)\""
    assert bash(cmd) == "ask"


@pytest.mark.xfail(strict=True, reason="KNOWN LIMITATION: encoded payloads hide markers from text inspection")
def test_KNOWN_LIMIT_base64_payload_is_not_detected():
    cmd = "python -c \"import base64; exec(base64.b64decode('aW1wb3J0IGh0dHB4'))\""
    assert bash(cmd) == "ask"


@pytest.mark.xfail(strict=True, reason="KNOWN LIMITATION: a command file outside the working tree that the shell loads")
def test_KNOWN_LIMIT_alias_defined_elsewhere_is_not_detected():
    assert bash("deploy_everything") == "ask"


# ----------------------------------------------------------------------------- guard_edits
def test_edit_guard_denies_env_files_and_secrets():
    assert edit("C:/x/backend/.env", content="A=1") == "deny"
    assert edit("app/config.py", content=f"KEY='{FAKE_KEY}'") == "deny"
    assert GE.decide({"file_path": "x.py", "edits": [{"new_string": FAKE_RSA}]})[0] == "deny"
    # deny beats ask: a secret written into a guardrail file is still denied
    assert edit(".claude/hooks/guard_bash.py", content=f"K='{FAKE_KEY}'") == "deny"


@pytest.mark.parametrize(
    "path",
    ["backend/.env", ".env", "backend/live.env", "prod.env", "frontend/.env.local", ".env.production", "x/.ENV"],
)
def test_REVIEW_M2_every_env_style_file_is_denied(path):
    assert edit(path, content="YOUCAM_MODE=live") == "deny", path
    assert edit_proc(path, content="YOUCAM_MODE=live") == "deny", path


@pytest.mark.parametrize(
    "path",
    [
        "C:/Users/USER/glowcue/.claude/hooks/guard_bash.py",
        ".claude/hooks/guard_edits.py",
        ".claude/hooks/format_python.py",
        ".claude/settings.json",
        ".claude/settings.local.json",
        ".Claude/Hooks/guard_bash.py",  # mixed case
        ".githooks/pre-commit",
        "scripts/security/secret_patterns.py",
        "scripts/security/check_secrets.py",
        "scripts/tests/test_security_guards.py",
        "scripts/validate_project.py",
        ".github/workflows/ci.yml",
        ".gitignore",
        "C:\\Users\\USER\\glowcue\\.claude\\settings.json",
    ],
)
def test_edit_guard_asks_owner_for_guardrail_files(path):
    assert edit(path, content="# change") == "ask", path
    assert edit_proc(path, content="# change") == "ask", path


def test_edit_guard_allows_normal_files():
    assert edit("backend/.env.example", content="YOUCAM_API_KEY=your_api_key_here") == "allow"
    assert edit("frontend/.env.example", content="VITE_API_BASE_URL=http://localhost:8000") == "allow"
    assert edit("app/main.py", new_string="app = FastAPI()") == "allow"
    assert edit(".claude/skills/x/SKILL.md", content="# skill") == "allow"
    assert edit(".claude/rules/backend.md", content="# rule") == "allow"
    assert edit("scripts/tests/test_x.py", content="def test_x(): pass") == "allow"
    assert edit("ruff.toml", content="line-length = 120") == "allow"  # documented: formatter config is not a guardrail


# ----------------------------------------------------------------------------- REVIEW M3: fail closed
def run_main(module, stdin_text: str, monkeypatch, capsys):
    monkeypatch.setattr(sys, "stdin", io.StringIO(stdin_text))
    with pytest.raises(SystemExit) as exc:
        module.main()
    out = capsys.readouterr()
    code = exc.value.code
    return (2 if code == 2 else 0), out.out, out.err


def verdict_from(code: int, stdout: str) -> str:
    if code == 2:
        return "deny"
    return json.loads(stdout)["hookSpecificOutput"]["permissionDecision"] if stdout.strip() else "allow"


MALFORMED_INPUTS = [
    "not json at all",
    "",
    "{",
    "null",
    "[]",
    "{}",
    '{"tool_input": null}',
    '{"tool_input": []}',
    '{"tool_input": "ls"}',
    '{"tool_input": 5}',
]


@pytest.mark.parametrize("raw", MALFORMED_INPUTS)
def test_REVIEW_M3_bash_guard_fails_closed_on_bad_input(raw, monkeypatch, capsys):
    code, out, _ = run_main(GB, raw, monkeypatch, capsys)
    assert verdict_from(code, out) == "ask", repr(raw)


@pytest.mark.parametrize("raw", MALFORMED_INPUTS)
def test_REVIEW_M3_edit_guard_fails_closed_on_bad_input(raw, monkeypatch, capsys):
    code, out, _ = run_main(GE, raw, monkeypatch, capsys)
    assert verdict_from(code, out) == "ask", repr(raw)


def test_REVIEW_M3_command_of_wrong_type_asks(monkeypatch, capsys):
    code, out, _ = run_main(GB, json.dumps({"tool_input": {"command": 123}}), monkeypatch, capsys)
    assert verdict_from(code, out) == "ask"
    code, out, _ = run_main(GB, json.dumps({"tool_input": {"command": ["ls"]}}), monkeypatch, capsys)
    assert verdict_from(code, out) == "ask"


def test_tool_call_without_a_command_is_allowed(monkeypatch, capsys):
    code, out, _ = run_main(GB, json.dumps({"tool_input": {"description": "no command here"}}), monkeypatch, capsys)
    assert verdict_from(code, out) == "allow"


def test_REVIEW_M3_unexpected_exception_in_bash_guard_asks(monkeypatch, capsys):
    def boom(*_a, **_k):
        raise RuntimeError("simulated bug")

    monkeypatch.setattr(GB, "tokenize", boom)
    code, out, _ = run_main(GB, json.dumps({"tool_input": {"command": "ls"}}), monkeypatch, capsys)
    assert verdict_from(code, out) == "ask"
    assert "internal error" in out


def test_REVIEW_M3_unexpected_exception_in_edit_guard_asks(monkeypatch, capsys):
    def boom(*_a, **_k):
        raise RuntimeError("simulated bug")

    monkeypatch.setattr(GE, "decide", boom)
    code, out, _ = run_main(GE, json.dumps({"tool_input": {"file_path": "x.py", "content": "x"}}), monkeypatch, capsys)
    assert verdict_from(code, out) == "ask"


def test_REVIEW_M3_import_failure_degrades_to_ask_and_still_denies_secrets(tmp_path):
    """CLAUDE_PROJECT_DIR points at a tree without scripts/security, so the shared patterns cannot be imported."""
    bare = tmp_path
    # bash guard
    assert decision(run_hook("guard_bash.py", {"tool_input": {"command": "ls"}}, project_dir=bare)) == "allow"
    assert decision(run_hook("guard_bash.py", {"tool_input": {"command": "python x.py"}}, project_dir=bare)) == "ask"
    assert (
        decision(run_hook("guard_bash.py", {"tool_input": {"command": f"echo {FAKE_KEY}"}}, project_dir=bare)) == "deny"
    )
    assert (
        decision(run_hook("guard_bash.py", {"tool_input": {"command": "cat backend/.env"}}, project_dir=bare)) == "deny"
    )
    # edit guard
    assert (
        decision(run_hook("guard_edits.py", {"tool_input": {"file_path": "any.py", "content": "x"}}, project_dir=bare))
        == "ask"
    )
    assert (
        decision(
            run_hook("guard_edits.py", {"tool_input": {"file_path": "a.py", "content": FAKE_KEY}}, project_dir=bare)
        )
        == "deny"
    )
    assert (
        decision(
            run_hook("guard_edits.py", {"tool_input": {"file_path": "backend/.env", "content": "A"}}, project_dir=bare)
        )
        == "deny"
    )


def test_REVIEW_M3_bad_input_through_the_real_process_protocol():
    assert decision(run_hook("guard_bash.py", None, raw="not json")) == "ask"
    assert decision(run_hook("guard_edits.py", None, raw="not json")) == "ask"
    assert decision(run_hook("guard_bash.py", None, raw='{"tool_input": []}')) == "ask"


# ----------------------------------------------------------------------------- settings.json wiring
@pytest.fixture(scope="module")
def settings() -> dict:
    return json.loads((ROOT / ".claude" / "settings.json").read_text(encoding="utf-8"))


def pretool_hooks(settings: dict) -> list[tuple[str, dict]]:
    return [(g["matcher"], h) for g in settings["hooks"]["PreToolUse"] for h in g["hooks"]]


def test_settings_blocks_when_guard_hooks_fail(settings):
    hooks = pretool_hooks(settings)
    assert len(hooks) >= 2
    for _matcher, hook in hooks:
        assert hook.get("onFailure") == "block", "a crashing or timed-out guard must block the action"
        assert hook.get("shell") == "bash"
        assert hook["command"].rstrip().endswith("|| exit 2"), "missing interpreter must block (exit 2)"


def test_settings_guards_cover_all_command_running_tools(settings):
    matchers = {m for m, h in pretool_hooks(settings) if "guard_bash" in h["command"]}
    assert matchers and all({"Bash", "PowerShell", "Monitor"} <= set(m.split("|")) for m in matchers)
    edit_matchers = {m for m, h in pretool_hooks(settings) if "guard_edits" in h["command"]}
    assert edit_matchers and all(
        {"Write", "Edit", "MultiEdit", "NotebookEdit"} <= set(m.split("|")) for m in edit_matchers
    )


def test_settings_native_rules_back_up_the_hooks(settings):
    perms = settings["permissions"]
    asks, denies = set(perms["ask"]), set(perms["deny"])
    assert {"Bash(*makeupar.com*)", "Bash(*yce-api*)", "Bash(*YOUCAM_MODE=live*)"} <= asks
    assert {
        "Edit(/.claude/hooks/**)",
        "Edit(/.claude/settings.json)",
        "Edit(/.githooks/**)",
        "Edit(/scripts/security/**)",
    } <= asks
    assert {
        "Read(**/.env)",
        "Read(**/*.env)",
        "Edit(**/.env)",
        "Edit(**/*.env)",
        "Edit(/.claude/settings.local.json)",
    } <= denies
    assert not any(".env.example" in rule for rule in denies | asks), "examples must stay readable and editable"
    assert perms["disableBypassPermissionsMode"] == "disable"
    assert perms.get("defaultMode") != "bypassPermissions"
    assert not any("LIVE_APPROVED" in rule for rule in perms["allow"]), "no allow rule may pre-approve live calls"


def test_REVIEW_M3_hook_command_blocks_when_python_is_missing(settings):
    """Run the exact settings command with the interpreter replaced by a name that does not exist."""
    bash_exe = shutil.which("bash")
    if not bash_exe:
        pytest.skip("bash not available")
    hook = next(h for _m, h in pretool_hooks(settings) if "guard_bash" in h["command"])
    command = hook["command"].replace("python ", "definitely-not-python-xyz ", 1)
    proc = subprocess.run(
        [bash_exe, "-c", command],
        capture_output=True,
        text=True,
        env={**os.environ, "CLAUDE_PROJECT_DIR": str(ROOT)},
        input="{}",
    )
    assert proc.returncode == 2, (proc.returncode, proc.stderr)


def test_REVIEW_M3_hook_command_blocks_when_the_script_crashes(settings, tmp_path):
    bash_exe = shutil.which("bash")
    if not bash_exe:
        pytest.skip("bash not available")
    crashing = tmp_path / "crash.py"
    crashing.write_text("raise SystemExit(1)\n", encoding="utf-8")
    hook = next(h for _m, h in pretool_hooks(settings) if "guard_bash" in h["command"])
    command = hook["command"].replace('"${CLAUDE_PROJECT_DIR}/.claude/hooks/guard_bash.py"', f'"{crashing.as_posix()}"')
    proc = subprocess.run([bash_exe, "-c", command], capture_output=True, text=True, input="{}")
    assert proc.returncode == 2


def test_every_hook_script_named_in_settings_exists(settings):
    for event in settings["hooks"].values():
        for group in event:
            for hook in group["hooks"]:
                for script in __import__("re").findall(r"\.claude/hooks/[\w.]+\.py", hook["command"]):
                    assert (ROOT / script).is_file(), script
