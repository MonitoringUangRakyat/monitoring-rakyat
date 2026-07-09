from __future__ import annotations

import re
import os
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

SKIP_DIRS = {
    ".git",
    "__pycache__",
    ".pytest_cache",
    "node_modules",
    ".venv",
    "venv",
}

PATTERNS = [
    ("windows_user_path", re.compile(r"C:\\Users\\[^\\\s\"']+", re.IGNORECASE)),
    ("local_loopback", re.compile(r"\b(127\.0\.0\.1|localhost)\b", re.IGNORECASE)),
    ("private_ipv4", re.compile(r"\b(10\.0\.|192\.168\.|172\.(1[6-9]|2[0-9]|3[0-1])\.)")),
    ("codex_private_dir", re.compile(r"(\.codex|\.agents)", re.IGNORECASE)),
    ("openai_key", re.compile(r"\bsk-(proj-|live|test|ant-)?[A-Za-z0-9_]{16,}")),
    ("github_token", re.compile(r"\b(ghp_[0-9A-Za-z]{20,}|github_pat_[0-9A-Za-z_]{20,})")),
    ("google_token", re.compile(r"\bAIza[0-9A-Za-z_-]{20,}")),
    ("private_key", re.compile(r"BEGIN (RSA|OPENSSH|PRIVATE) KEY")),
]

for marker in (os.environ.get("ANON_MARKERS") or "").split(","):
    marker = marker.strip()
    if marker:
        PATTERNS.append(("personal_marker", re.compile(re.escape(marker), re.IGNORECASE)))


def iter_files(root: Path):
    for path in root.rglob("*"):
        if path.is_dir():
            continue
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        if path.name == "anonymity_scan.py":
            continue
        if path.suffix.lower() in {".png", ".jpg", ".jpeg", ".gif", ".webp", ".zip", ".db"}:
            continue
        yield path


def main() -> int:
    findings: list[str] = []
    for path in iter_files(ROOT):
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        for lineno, line in enumerate(text.splitlines(), 1):
            for name, pattern in PATTERNS:
                if pattern.search(line):
                    findings.append(f"{path.relative_to(ROOT)}:{lineno}: {name}")

    if findings:
        print("ANONYMITY_SCAN_FAILED")
        for item in findings[:200]:
            print(item)
        if len(findings) > 200:
            print(f"... {len(findings) - 200} more")
        return 1

    print("ANONYMITY_SCAN_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
