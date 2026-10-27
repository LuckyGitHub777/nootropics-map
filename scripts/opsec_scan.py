#!/usr/bin/env python3
"""Conservative public-boundary scan. Not a substitute for human OPSEC review."""
from __future__ import annotations
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TEXT_EXT = {".md", ".txt", ".html", ".css", ".js", ".mjs", ".json", ".yml", ".yaml", ".cff", ".toml"}
SKIP_DIRS = {".git", "node_modules", "dist", "coverage", "__pycache__"}

PATTERNS = {
    "private key": re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----"),
    "github token": re.compile(r"\b(?:ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9]{30,}\b"),
    "generic api secret": re.compile(r"(?i)\b(?:api[_-]?key|secret[_-]?key|access[_-]?token)\s*[:=]\s*['\"][^'\"]{8,}['\"]"),
    "aws access key": re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
}

# Public-source URLs are expected. Raw e-mail addresses are not required in v0.1 public content.
EMAIL = re.compile(r"(?<![\w.-])[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}(?![\w.-])")
EMAIL_ALLOW = set()


def main() -> int:
    findings = []
    forbidden_names = {".env", ".env.local", "id_rsa", "id_ed25519"}
    for path in ROOT.rglob("*"):
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        if path.is_file() and path.name in forbidden_names:
            findings.append((path, "forbidden filename"))
        if not path.is_file() or path.suffix.lower() not in TEXT_EXT:
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        for label, pattern in PATTERNS.items():
            if pattern.search(text):
                findings.append((path, label))
        for email in EMAIL.findall(text):
            if email not in EMAIL_ALLOW:
                findings.append((path, f"unexpected email address: {email}"))

    if findings:
        print("OPSEC SCAN: FAIL")
        for path, reason in findings:
            print(f" - {path.relative_to(ROOT)}: {reason}")
        return 1
    print("OPSEC SCAN: PASS — no obvious credential/private-contact patterns detected")
    return 0


if __name__ == "__main__":
    sys.exit(main())
