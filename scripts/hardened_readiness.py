from __future__ import annotations

import csv
import json
import re
from collections import Counter
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from evidence_policy import publication_decision

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "gudang-db"
ACTIVE = ROOT / "dashboard" / "active-period.json"
OUT = ROOT / "dashboard" / "publication_readiness.json"
CORE = {"akuntansi","audit","audittrail","bea_cukai","bumn","korupsi","pajak","parpol","prog_daerah","prog_eksekutif","prog_legislatif","redflag","risknas","sda","vendor"}

def module_year(path: Path):
    m = re.match(r"(.+)_((?:19|20)\d{2})\.csv$", path.name, re.I)
    return (m.group(1), int(m.group(2))) if m else (path.stem, 0)

def rows(path: Path):
    with path.open("r", encoding="utf-8-sig", newline="") as h:
        for row in csv.DictReader(h):
            clean={str(k or "").strip():str(v or "").strip() for k,v in row.items()}
            if any(clean.values()): yield clean

def main() -> int:
    active=json.loads(ACTIVE.read_text(encoding="utf-8"))
    now=datetime.now(ZoneInfo("Asia/Jakarta"))
    counts={m:{"rows":0,"publishable":0,"quarantined":0} for m in sorted(CORE)}
    reasons=Counter()
    for path in DB.rglob("*.csv"):
        mod, year=module_year(path)
        if mod not in counts or year != int(active["year"]): continue
        for row in rows(path):
            counts[mod]["rows"] += 1
            d=publication_decision(row)
            if d.allowed: counts[mod]["publishable"] += 1
            else:
                counts[mod]["quarantined"] += 1
                reasons[d.reason] += 1
    blockers=[]
    if (int(active["year"]),int(active["month"])) != (now.year,now.month): blockers.append("ACTIVE_PERIOD_STALE")
    payload={"generated_at":now.isoformat(timespec="seconds"),"status":"PASS" if not blockers else "NEEDS_WORK","blockers":blockers,"semantics":"RILL = explicit publishable status + evidence/source. Source+money alone is never sufficient.","core_modules":counts,"quarantine_reasons":dict(reasons)}
    OUT.write_text(json.dumps(payload,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(f"Hardened readiness: {payload['status']}")
    return 1 if blockers else 0

if __name__=="__main__":
    raise SystemExit(main())
