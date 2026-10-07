from __future__ import annotations

import csv
import hashlib
import json
import re
from collections import Counter
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from evidence_policy import has_money, has_source, publication_decision

ROOT = Path(__file__).resolve().parents[1]
GUDANG_DB = ROOT / "gudang-db"
OUT = ROOT / "dashboard" / "evidence_recovery_tasks.json"
INVENTORY = ROOT / "dashboard" / "verification_inventory.json"


def module_year(path: Path):
    m = re.match(r"(.+)_((?:19|20)\d{2})\.csv$", path.name, re.I)
    return (m.group(1), int(m.group(2))) if m else (path.stem, 0)


def rows(path: Path):
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        for idx, row in enumerate(csv.DictReader(handle), start=2):
            clean = {str(k or "").strip(): str(v or "").strip() for k, v in row.items()}
            if any(clean.values()):
                yield idx, clean


def row_ref(row, line):
    for key in ("col", "id", "ID", "record_id", "No_Perkara", "No_Bukti"):
        if row.get(key):
            return str(row[key])[:160]
    return f"line:{line}"


def main() -> int:
    now = datetime.now(ZoneInfo("Asia/Jakarta")).isoformat(timespec="seconds")
    tasks = []
    counts = Counter()
    for path in sorted(GUDANG_DB.rglob("*.csv")):
        rel = path.relative_to(GUDANG_DB)
        if any(p.startswith("_") for p in rel.parts[:-1]):
            continue
        module, year = module_year(path)
        for line, row in rows(path):
            decision = publication_decision(row)
            counts["rows_scanned"] += 1
            counts["publishable" if decision.allowed else "quarantined"] += 1
            counts[f"reason:{decision.reason}"] += 1
            if decision.allowed:
                continue
            if not (has_money(row) or has_source(row) or any(row.get(k) for k in ("Kasus", "Nama_Kasus", "Program", "Jenis"))):
                continue
            ref = row_ref(row, line)
            digest = hashlib.sha256(f"{rel}|{ref}|{decision.reason}".encode()).hexdigest()[:16].upper()
            tasks.append({
                "task_id": f"EVID-{digest}",
                "task": "resolve_evidence_and_verification",
                "status": "ACTIVE",
                "priority": "HIGH" if has_money(row) else "MEDIUM",
                "module": module,
                "year": year,
                "file": str(rel).replace("\\", "/"),
                "record_ref": ref,
                "reason": decision.reason,
                "status_snapshot": decision.status,
                "has_source": has_source(row),
                "has_money": has_money(row),
                "next_action": "Cross-check official source, validate semantic amount/period/entity, then explicitly promote status. Never fabricate missing evidence.",
            })
    OUT.write_text(json.dumps(tasks, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    INVENTORY.write_text(json.dumps({
        "generated_at": now,
        "counts": dict(counts),
        "tasks": len(tasks),
        "policy": "Every non-publishable substantive record becomes explicit recovery work.",
    }, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    print(f"Evidence recovery tasks: {len(tasks)}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
