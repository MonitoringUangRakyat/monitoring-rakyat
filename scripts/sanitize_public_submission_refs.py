from __future__ import annotations

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TARGET_DIRS = [
    ROOT / "gudang-db",
    ROOT / "dashboard",
    ROOT / "docs",
]
TEXT_SUFFIXES = {".csv", ".json", ".md", ".html", ".txt"}
ISSUE_URL = re.compile(r"https://github\.com/MonitoringUangRakyat/monitoring-rakyat/issues/(\d+)", re.IGNORECASE)
ISSUE_NOTE = re.compile(r"kontribusi publik issue #(\d+)", re.IGNORECASE)
ISSUE_NOTE_EN = re.compile(r"public-submission issues?", re.IGNORECASE)


def sanitize_text(text: str) -> tuple[str, int]:
    changes = 0

    def repl_url(match: re.Match[str]) -> str:
        nonlocal changes
        changes += 1
        return f"ANON_PUBLIC_SUBMISSION:ISSUE-{match.group(1)}"

    text = ISSUE_URL.sub(repl_url, text)
    text, note_changes = ISSUE_NOTE.subn("kontribusi publik anonim", text)
    changes += note_changes
    text, label_changes = ISSUE_NOTE_EN.subn("public submissions", text)
    changes += label_changes
    return text, changes


def iter_files() -> list[Path]:
    files: list[Path] = []
    for folder in TARGET_DIRS:
        if not folder.exists():
            continue
        for path in folder.rglob("*"):
            if path.is_file() and path.suffix.lower() in TEXT_SUFFIXES:
                files.append(path)
    return files


def main() -> int:
    changed_files = 0
    total_changes = 0
    for path in iter_files():
        original = path.read_text(encoding="utf-8-sig", errors="ignore")
        sanitized, changes = sanitize_text(original)
        if not changes:
            continue
        path.write_text(sanitized, encoding="utf-8")
        changed_files += 1
        total_changes += changes
    print(f"Sanitized public submission refs: files={changed_files} replacements={total_changes}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
