"""Single source of truth for GlowCue secret detection.

Imported by:
  - scripts/security/check_secrets.py   (git pre-commit hook + CI)
  - .claude/hooks/guard_edits.py         (Claude Code PreToolUse hook)
  - .claude/hooks/guard_bash.py          (Claude Code PreToolUse hook)

Keep patterns specific enough to avoid false positives on documentation placeholders
such as `your_api_key_here` or `Bearer YOUR_API_KEY`.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import PurePosixPath


@dataclass(frozen=True)
class Finding:
    rule: str
    line: int
    excerpt: str


SECRET_PATTERNS: dict[str, re.Pattern[str]] = {
    # YouCam / OpenAI-style secret keys: "sk-" followed by a long token.
    "sk_api_key": re.compile(r"\bsk-[A-Za-z0-9_\-]{32,}"),
    # DER/base64 RSA public key blob as shown in the YouCam console ("secret key").
    "rsa_key_blob": re.compile(r"MIGfMA0GCSqGSIb3DQEBAQUAA4GNADCB[A-Za-z0-9+/=]{40,}"),
    "private_key_pem": re.compile(r"-----BEGIN (?:RSA |EC |DSA |OPENSSH |PGP )?PRIVATE KEY-----"),
    "github_token": re.compile(r"\bgh[pousr]_[A-Za-z0-9]{36,}\b"),
    "aws_access_key": re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    "bearer_literal": re.compile(r"(?i)\bbearer\s+(?!YOUR_|\$|\{|<|\")[A-Za-z0-9_\-.=]{30,}"),
    # key = "long literal" style assignments (ignores env lookups and placeholders)
    "generic_assignment": re.compile(
        r"(?i)\b(?:api[_-]?key|secret[_-]?key|access[_-]?token|auth[_-]?token|password)\b"
        r"\s*[:=]\s*['\"]?(?!your_|<|\$|\{|os\.|process\.|settings\.|env\b|none\b|null\b)"
        r"[A-Za-z0-9_\-+/=]{24,}"
    ),
}

PLACEHOLDER_ALLOWLIST = ("your_api_key_here", "YOUR_API_KEY", "example", "placeholder")

# Files that must never be committed.
FORBIDDEN_PATH_PATTERNS = (
    re.compile(r"(^|/)\.env$"),
    re.compile(r"(^|/)\.env\.(?!example$)[^/]+$"),
    re.compile(r"\.(pem|key|p12|pfx)$", re.I),
    re.compile(r"(^|/)private/"),
    re.compile(r"(^|/)backend/app/fixtures/raw/"),
    re.compile(r"(^|/)\.claude/settings\.local\.json$"),
)

# Photographs may contain faces (personal data). They are only allowed in these folders,
# and anywhere else only with explicit owner approval (GLOWCUE_PHOTO_APPROVED=1).
PHOTO_EXTENSIONS = {".jpg", ".jpeg", ".heic", ".heif", ".webp"}
PHOTO_ALLOWED_PREFIXES = ("frontend/public/products/", "docs/screenshots/", ".github/")


def scan_text(text: str) -> list[Finding]:
    findings: list[Finding] = []
    for lineno, line in enumerate(text.splitlines(), start=1):
        if any(p in line for p in PLACEHOLDER_ALLOWLIST) and "sk-" not in line:
            continue
        for rule, pattern in SECRET_PATTERNS.items():
            m = pattern.search(line)
            if m:
                token = m.group(0)
                redacted = token[:6] + "…" + f"[{len(token)} chars]"
                findings.append(Finding(rule, lineno, redacted))
    return findings


def forbidden_path_reason(path: str, photo_approved: bool = False) -> str | None:
    p = path.replace("\\", "/")
    for pattern in FORBIDDEN_PATH_PATTERNS:
        if pattern.search(p):
            return f"forbidden file type/location ({pattern.pattern})"
    is_photo = PurePosixPath(p).suffix.lower() in PHOTO_EXTENSIONS
    if is_photo and not photo_approved and not p.startswith(PHOTO_ALLOWED_PREFIXES):
        return "photograph outside approved folders (set GLOWCUE_PHOTO_APPROVED=1 only with owner approval)"
    return None
