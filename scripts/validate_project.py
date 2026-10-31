"""Validate the GlowCue engineering system: config files, skills, agents, rules, hooks and doc links.

Usage: python scripts/validate_project.py
Exit code 0 = all checks passed, 1 = at least one failure. Fast (< 2 s); safe to run anytime.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
failures: list[str] = []
passes = 0


def check(cond: bool, msg: str) -> None:
    global passes
    if cond:
        passes += 1
    else:
        failures.append(msg)


def frontmatter(path: Path) -> dict[str, str]:
    """Minimal YAML frontmatter reader: top-level `key: value` pairs (lists/blocks kept as raw text)."""
    text = path.read_text(encoding="utf-8")
    m = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    if not m:
        return {}
    data: dict[str, str] = {}
    key = None
    for line in m.group(1).splitlines():
        km = re.match(r"^([A-Za-z_][\w-]*):\s*(.*)$", line)
        if km:
            key, value = km.group(1), km.group(2).strip()
            data[key] = value
        elif key and line.startswith((" ", "-")):
            data[key] = (data[key] + " " + line.strip()).strip()
    return data


def valid_scalar(value: str) -> bool:
    """Reject the YAML mistake of several quoted strings separated by commas."""
    return not re.match(r'^"[^"]*"\s*,', value)


# 1. Required files
REQUIRED = [
    "CLAUDE.md",
    "AGENTS.md",
    "README.md",
    "LICENSE",
    ".gitignore",
    ".editorconfig",
    ".gitattributes",
    "ruff.toml",
    ".claude/settings.json",
    ".githooks/pre-commit",
    ".github/workflows/ci.yml",
    ".github/PULL_REQUEST_TEMPLATE.md",
    ".github/CONTRIBUTING.md",
    ".agents/rules/antigravity-reviewer.md",
    "backend/.env.example",
    "backend/requirements.txt",
    "backend/requirements-dev.txt",
    "frontend/package.json",
    "frontend/.env.example",
    "docs/README.md",
    "docs/PROJECT_STATUS.md",
    "docs/IMPLEMENTATION_ROADMAP.md",
    "docs/YOUCAM_API.md",
    "docs/SECURITY_PRIVACY.md",
    "docs/RUNBOOK.md",
]
for rel in REQUIRED:
    check((ROOT / rel).is_file(), f"missing required file: {rel}")

# 2. settings.json: valid JSON, no bypass, hook scripts exist
settings_path = ROOT / ".claude/settings.json"
try:
    settings = json.loads(settings_path.read_text(encoding="utf-8"))
    perms = settings.get("permissions", {})
    check(perms.get("disableBypassPermissionsMode") == "disable", "settings: bypass mode must be disabled")
    check(perms.get("defaultMode") != "bypassPermissions", "settings: defaultMode must not be bypassPermissions")
    check(any(".env" in r for r in perms.get("deny", [])), "settings: .env deny rules missing")
    for event, groups in settings.get("hooks", {}).items():
        for group in groups:
            for hook in group.get("hooks", []):
                for script in re.findall(r"\.claude/hooks/[\w.]+\.py", hook.get("command", "")):
                    check((ROOT / script).is_file(), f"settings: {event} hook script missing: {script}")
except (OSError, json.JSONDecodeError) as exc:
    failures.append(f"settings.json invalid: {exc}")

# 3. Skills
skills = sorted((ROOT / ".claude/skills").glob("*/SKILL.md"))
check(len(skills) >= 12, f"expected >= 12 skills, found {len(skills)}")
for skill in skills:
    fm = frontmatter(skill)
    name = skill.parent.name
    check(fm.get("name") == name, f"skill {name}: frontmatter name must equal directory name")
    check(len(fm.get("description", "")) >= 40, f"skill {name}: description missing or too short")
    for key, value in fm.items():
        check(valid_scalar(value), f"skill {name}: invalid YAML scalar in '{key}'")
    check(len(fm.get("description", "") + fm.get("when_to_use", "")) <= 1536, f"skill {name}: description too long")

# 4. Agents
agents = sorted((ROOT / ".claude/agents").glob("*.md"))
check(len(agents) >= 7, f"expected >= 7 agents, found {len(agents)}")
for agent in agents:
    fm = frontmatter(agent)
    check(bool(fm.get("name")) and ":" not in fm.get("name", ":"), f"agent {agent.name}: invalid name")
    check(len(fm.get("description", "")) >= 40, f"agent {agent.name}: description missing")
    tools = fm.get("tools", "")
    check(
        "Edit" not in tools.split(", ") and "Write" not in tools,
        f"agent {agent.name}: reviewers must not have Edit/Write",
    )

# 5. Rules: path-scoped ones must declare paths
for rule in sorted((ROOT / ".claude/rules").glob("*.md")):
    fm = frontmatter(rule)
    if rule.stem in {"backend", "frontend", "testing", "api-integration", "documentation"}:
        check("paths" in fm and "**" in fm["paths"] or "/" in fm.get("paths", ""), f"rule {rule.name}: paths missing")

# 6. Secrets hygiene
ignored = subprocess.run(["git", "check-ignore", "-q", "backend/.env"], cwd=ROOT).returncode == 0
check(ignored, "backend/.env is NOT gitignored")
example = (ROOT / "backend/.env.example").read_text(encoding="utf-8").strip()
check(example == "YOUCAM_API_KEY=your_api_key_here", "backend/.env.example must contain only the placeholder line")

# 7. Relative markdown links resolve
LINK = re.compile(r"\[[^\]]*\]\((?!https?://|mailto:|#)([^)#\s]+)(?:#[^)]*)?\)")
md_files = [p for p in ROOT.rglob("*.md") if not any(part in {"node_modules", ".venv", "dist"} for part in p.parts)]
for md in md_files:
    text = md.read_text(encoding="utf-8", errors="replace")
    text = re.sub(r"```.*?```", "", text, flags=re.S)
    for target in LINK.findall(text):
        resolved = (md.parent / target).resolve()
        check(resolved.exists(), f"broken link in {md.relative_to(ROOT)}: {target}")

print(f"validate_project: {passes} checks passed, {len(failures)} failed")
for f in failures:
    print(f"  FAIL: {f}")
sys.exit(1 if failures else 0)
