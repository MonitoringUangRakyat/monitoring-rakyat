from __future__ import annotations

import csv
import hashlib
import json
import re
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from evidence_policy import publication_decision

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "gudang-db"
ACTIVE = ROOT / "dashboard" / "active-period.json"
OUT = ROOT / "dashboard" / "backfill_tasks.json"
STATUS = ROOT / "dashboard" / "backfill_status.json"
CORE_MODULES = ["akuntansi", "audit", "bea_cukai", "bumn", "korupsi", "pajak", "sda", "vendor"]
MIN_YEARS = 12

def module_year(path: Path):
    m = re.match(r"(.+)_((?:19|20)\d{2})\.csv$", path.name, re.I)
    return (m.group(1), int(m.group(2))) if m else (path.stem, 0)

def rows(path: Path):
    with path.open("r", encoding="utf-8-sig", newline="") as h:
        for row in csv.DictReader(h):
            clean = {str(k or "").strip(): str(v or "").strip() for k, v in row.items()}
            if any(clean.values()):
                yield clean

def main() -> int:
    active = json.loads(ACTIVE.read_text(encoding="utf-8"))
    end_year = int(active["year"])
    start_year = end_year - MIN_YEARS + 1
    counts = {(m, y): 0 for m in CORE_MODULES for y in range(start_year, end_year + 1)}
    raw_counts = {(m, y): 0 for m in CORE_MODULES for y in range(start_year, end_year + 1)}

    for path in DB.rglob("*.csv"):
        mod, year = module_year(path)
        if (mod, year) not in counts:
            continue
        for row in rows(path):
            raw_counts[(mod, year)] += 1
            if publication_decision(row).allowed:
                counts[(mod, year)] += 1

    now = datetime.now(ZoneInfo("Asia/Jakarta"))
    tasks = []
    for module in CORE_MODULES:
        for year in range(start_year, end_year + 1):
            verified = counts[(module, year)]
            if verified:
                continue
            raw = raw_counts[(module, year)]
            digest = hashlib.sha256(f"backfill|{module}|{year}".encode()).hexdigest()[:16].upper()
            tasks.append({
                "task_id": f"BACKFILL-{digest}",
                "task": "backfill_official_evidence",
                "status": "ACTIVE",
                "priority": "HIGH" if year >= end_year - 2 else "MEDIUM",
                "module": module,
                "year": year,
                "verified_rows": verified,
                "existing_unverified_rows": raw,
                "reason": "NO_PUBLISHABLE_VERIFIED_RECORD_FOR_MODULE_YEAR",
                "next_action": "Search official/primary sources, capture document/hash/citation, normalize, validate, then explicitly promote. Never seed a guessed numeric value.",
                "created_at": now.isoformat(timespec="seconds"),
            })

    OUT.write_text(json.dumps(tasks, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    status = {
        "generated_at": now.isoformat(timespec="seconds"),
        "year_range": [start_year, end_year],
        "modules": CORE_MODULES,
        "missing_verified_module_years": len(tasks),
        "policy": "MISSING_HISTORY_BECOMES_A_TASK_NOT_A_FAKE_BASELINE",
    }
    STATUS.write_text(json.dumps(status, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Backfill tasks: {len(tasks)} module-years missing verified evidence")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
