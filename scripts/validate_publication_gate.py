from __future__ import annotations

import argparse
import csv
import json
import re
from collections import Counter
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from evidence_policy import loss_amount, publication_decision, recovery_amount

ROOT = Path(__file__).resolve().parents[1]
GUDANG_DB = ROOT / "gudang-db"
ACTIVE_PERIOD = ROOT / "dashboard" / "active-period.json"
SUMMARY = ROOT / "dashboard" / "dashboard_summary.json"
OUT = ROOT / "dashboard" / "publication_gate_status.json"
REPORT = ROOT / "docs" / "PUBLICATION_GATE_REPORT.md"


def rows(path: Path):
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        for row in csv.DictReader(handle):
            clean = {str(k or "").strip(): str(v or "").strip() for k, v in row.items()}
            if any(clean.values()):
                yield clean


def path_module_year(path: Path) -> tuple[str, int]:
    match = re.match(r"(.+)_((?:19|20)\d{2})\.csv$", path.name, re.I)
    return (match.group(1), int(match.group(2))) if match else (path.stem, 0)


def row_year(row: dict[str, str], fallback: int) -> int:
    for key in ("tahun", "Tahun", "year", "Tahun_Data"):
        match = re.search(r"(19\d{2}|20\d{2})", str(row.get(key, "")))
        if match:
            return int(match.group(1))
    return fallback


def row_month(row: dict[str, str]) -> int:
    lower = {str(k).lower(): str(v or "").strip().lower() for k, v in row.items()}
    value = lower.get("bulan") or lower.get("bln") or lower.get("bulan_data") or lower.get("bln_thn") or ""
    names = {"januari":1,"februari":2,"maret":3,"april":4,"mei":5,"juni":6,"juli":7,"agustus":8,"september":9,"oktober":10,"november":11,"desember":12}
    if value in names:
        return names[value]
    match = re.search(r"(?:^|\D)(1[0-2]|0?[1-9])(?:\D|$)", value)
    return int(match.group(1)) if match else 0


def recompute() -> dict:
    active = json.loads(ACTIVE_PERIOD.read_text(encoding="utf-8"))
    ay, am = int(active["year"]), int(active["month"])
    verified_loss = verified_recovery = 0.0
    verified_cases = 0
    scanned = allowed = blocked = 0
    blocked_reasons = Counter()
    for path in sorted(GUDANG_DB.rglob("*.csv")):
        rel = path.relative_to(GUDANG_DB)
        if any(part.startswith("_") for part in rel.parts[:-1]):
            continue
        module, fy = path_module_year(path)
        if "korup" not in module.lower():
            continue
        for row in rows(path):
            scanned += 1
            decision = publication_decision(row)
            if not decision.allowed:
                blocked += 1
                blocked_reasons[decision.reason] += 1
                continue
            allowed += 1
            if row_year(row, fy) == ay and row_month(row) == am:
                lower = {str(k).lower(): str(v or "").strip() for k, v in row.items()}
                if any(lower.get(k) for k in ("kasus", "nama_kasus", "kasus_terkait")):
                    verified_cases += 1
                verified_loss += loss_amount(row)
                verified_recovery += recovery_amount(row)
    return {
        "verified_current_period_loss": round(verified_loss),
        "verified_current_period_recovery": round(verified_recovery),
        "verified_current_period_cases": verified_cases,
        "corruption_rows_scanned": scanned,
        "corruption_rows_publishable": allowed,
        "corruption_rows_quarantined": blocked,
        "quarantine_reasons": dict(blocked_reasons),
    }


def evaluate() -> dict:
    active = json.loads(ACTIVE_PERIOD.read_text(encoding="utf-8"))
    summary = json.loads(SUMMARY.read_text(encoding="utf-8")) if SUMMARY.exists() else {}
    now = datetime.now(ZoneInfo("Asia/Jakarta"))
    truth = recompute()
    errors = []
    if (int(active.get("year",0)), int(active.get("month",0))) != (now.year, now.month):
        errors.append(f"STALE_ACTIVE_PERIOD: dashboard={active.get('month')}/{active.get('year')} Jakarta={now.month}/{now.year}")
    expected_pairs = {
        "kerugian_total": truth["verified_current_period_loss"],
        "recovery_total": truth["verified_current_period_recovery"],
        "jumlah_kasus": truth["verified_current_period_cases"],
    }
    for key, expected in expected_pairs.items():
        actual = int(summary.get(key, 0) or 0)
        if actual != int(expected):
            errors.append(f"SUMMARY_MISMATCH {key}: public={actual} verified_recompute={int(expected)}")
    gate = summary.get("publication_gate", {})
    if gate.get("mode") != "DEFAULT_DENY_EVIDENCE_FIRST":
        errors.append("SUMMARY_NOT_HARDENED: publication_gate.mode missing/default-allow")
    return {
        "generated_at": now.isoformat(timespec="seconds"),
        "status": "PASS" if not errors else "FAIL",
        "errors": errors,
        "recomputed": truth,
        "active_period": active,
        "summary_checked": {"kerugian_total": summary.get("kerugian_total"), "recovery_total": summary.get("recovery_total"), "jumlah_kasus": summary.get("jumlah_kasus"), "publication_gate": gate},
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--strict", action="store_true")
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    payload = evaluate()
    if args.write:
        OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
        REPORT.write_text("# Publication Gate Report\n\nStatus: **"+payload["status"]+"**\n\n```json\n"+json.dumps(payload, ensure_ascii=False, indent=2)+"\n```\n", encoding="utf-8")
    print(f"Publication gate: {payload['status']}")
    for err in payload["errors"]:
        print(f"ERROR: {err}")
    return 1 if args.strict and payload["errors"] else 0

if __name__ == "__main__":
    raise SystemExit(main())
