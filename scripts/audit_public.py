#!/usr/bin/env python3
"""Reject obvious secrets and private machine state before publication."""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKIP_DIRS = {".git", ".trash", ".obsidian", "plugins", "cache", "logs", "__pycache__"}
PATTERNS = [
    ("private key", re.compile(r"-----BEGIN (?:RSA |OPENSSH |EC |DSA )?PRIVATE KEY-----")),
    ("AWS access key", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
    ("GitHub token", re.compile(r"\bgh[pousr]_[A-Za-z0-9]{20,}\b")),
    ("Google API key", re.compile(r"\bAIza[0-9A-Za-z_-]{35}\b")),
    ("OpenAI-style secret key", re.compile(r"\bsk-[A-Za-z0-9_-]{24,}\b")),
    ("generic credential assignment", re.compile(r"(?i)\b(?:api[_-]?key|secret|password|token)\s*[:=]\s*[\"'][^\"']{12,}[\"']")),
    ("home-directory path", re.compile(r"/(?:home|Users|root)/[A-Za-z0-9_.-]+(?:/|$)")),
    ("Windows user path", re.compile(r"[A-Z]:\\Users\\[^\\\s]+", re.I)),
    ("WSL user path", re.compile(r"/mnt/[a-z]/Users/[^/\s]+", re.I)),
]

def main():
    errors = []
    for state_dir in (ROOT / ".obsidian" / "plugins", ROOT / ".obsidian" / "cache", ROOT / ".obsidian" / "logs"):
        if state_dir.exists() and any(state_dir.rglob("*")):
            errors.append(f"{state_dir.relative_to(ROOT)}: plugin/cache state must not be published")
    for path in ROOT.rglob("*"):
        if not path.is_file() or any(part in SKIP_DIRS for part in path.relative_to(ROOT).parts):
            continue
        if path.suffix.lower() in {".png", ".jpg", ".jpeg", ".gif", ".pdf", ".zip", ".pyc", ".db", ".sqlite"}:
            continue
        try: text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError): continue
        for label, pattern in PATTERNS:
            for match in pattern.finditer(text): errors.append(f"{path.relative_to(ROOT)}: possible {label} ({match.group(0)[:48]})")
    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1
    print("Public audit passed.")
    return 0

if __name__ == "__main__": raise SystemExit(main())
