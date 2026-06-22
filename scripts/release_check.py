from __future__ import annotations

import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REQUIRED = [
    "README.md",
    "LICENSE",
    "CONTRIBUTING.md",
    "DATA_GOVERNANCE.md",
    "SECURITY.md",
    "dashboard/index.html",
    "dashboard/app.js",
    "dashboard/active-period.json",
    "dashboard/dashboard_summary.json",
    "gudang-db/index.html",
    "gudang-db/_index/ai_index.json",
    "scripts/validate_gudang_db.py",
    "scripts/generate_ai_index.py",
    "scripts/build_dashboard_summary.py",
    "scripts/pre_github_readiness.py",
    "scripts/build_source_patrol.py",
    "scripts/ai_pengawas_orchestrator.py",
    "scripts/validate_immutable_db.py",
    "gudang-db/_ledger/immutable_index.json",
    "gudang-db/_ledger/deletion_requests.csv",
    "gudang-db/_ledger/restore_log.csv",
]
FORBIDDEN_TEXT = [
    "USERNAME" + "/monitoring-rakyat",
    "github.com/" + "USER/",
    "api_key",
    "telegram" + "_bot_token_here",
    "".join(["C:", "\\", "Users", "\\"]),
    "127" + ".0.0.1",
    "local" + "host:",
]
FORBIDDEN_FILES = [
    ".env",
    "secrets",
]


def run(args: list[str]) -> int:
    print("$", " ".join(args))
    return subprocess.call(args, cwd=ROOT)


def main() -> int:
    errors: list[str] = []

    for item in REQUIRED:
        if not (ROOT / item).exists():
            errors.append(f"Missing required file: {item}")

    for item in FORBIDDEN_FILES:
        if (ROOT / item).exists():
            errors.append(f"Forbidden local secret path exists: {item}")

    text_files = [
        path
        for path in ROOT.rglob("*")
        if path.is_file() and path.suffix.lower() in {".html", ".js", ".md", ".json", ".py", ".txt"}
        and path.name != "release_check.py"
    ]
    for path in text_files:
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        for marker in FORBIDDEN_TEXT:
            if marker in text:
                errors.append(f"Forbidden placeholder `{marker}` in {path.relative_to(ROOT)}")

    if errors:
        print("Release check failed:")
        for error in errors:
            print("ERROR:", error)
        return 1

    if run([sys.executable, "scripts/generate_ai_index.py"]) != 0:
        return 1
    if run([sys.executable, "scripts/validate_gudang_db.py"]) != 0:
        return 1
    if run([sys.executable, "scripts/validate_immutable_db.py"]) != 0:
        return 1
    if run([sys.executable, "scripts/build_dashboard_summary.py"]) != 0:
        return 1
    if run([sys.executable, "scripts/pre_github_readiness.py", "--write"]) != 0:
        return 1
    if run([sys.executable, "scripts/build_source_patrol.py"]) != 0:
        return 1
    if run([sys.executable, "scripts/ai_pengawas_orchestrator.py"]) != 0:
        return 1

    print("Release check passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
