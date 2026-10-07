from __future__ import annotations

import csv
import json
import re
from collections import Counter
from pathlib import Path

from evidence_policy import (
    loss_amount,
    publication_decision,
    recovery_amount,
)

ROOT = Path(__file__).resolve().parents[1]
GUDANG_DB = ROOT / "gudang-db"
ACTIVE_PERIOD = ROOT / "dashboard" / "active-period.json"
OUT = ROOT / "dashboard" / "dashboard_summary.json"


def iter_csv_rows(path: Path):
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        for row in csv.DictReader(handle):
            if any(str(value or "").strip() for value in row.values()):
                yield {str(k or "").strip(): str(v or "").strip() for k, v in row.items()}


def row_year(row: dict[str, str], fallback: int = 0) -> int:
    for key in ("tahun", "Tahun", "year", "tahun_data", "Tahun_Data"):
        value = row.get(key)
        if value:
            match = re.search(r"(19\d{2}|20\d{2})", value)
            if match:
                return int(match.group(1))
    return fallback


def row_month(row: dict[str, str]) -> int:
    lower = {str(k).strip().lower(): str(v or "").strip().lower() for k, v in row.items()}
    value = lower.get("bulan") or lower.get("bln") or lower.get("bulan_data") or lower.get("bln_thn") or ""
    names = {
        "januari": 1, "februari": 2, "maret": 3, "april": 4,
        "mei": 5, "juni": 6, "juli": 7, "agustus": 8,
        "september": 9, "oktober": 10, "november": 11, "desember": 12,
    }
    if value in names:
        return names[value]
    match = re.search(r"(?:^|\D)(1[0-2]|0?[1-9])(?:\D|$)", value)
    return int(match.group(1)) if match else 0


def main() -> None:
    active = json.loads(ACTIVE_PERIOD.read_text(encoding="utf-8"))
    active_year = int(active["year"])
    active_month = int(active["month"])
    trend_years = int(active.get("trend_years", 10))
    min_trend_year = active_year - trend_years + 1

    yearly_loss = {year: 0.0 for year in range(min_trend_year, active_year + 1)}
    active_loss = active_recovery = 0.0
    active_cases = active_actors = 0
    historical_cases = historical_actors = 0
    historical_cases_by_module: dict[str, int] = {}

    total_rows = published_rows = quarantined_rows = 0
    quarantine_reasons = Counter()

    for path in sorted(GUDANG_DB.rglob("*.csv")):
        rel = path.relative_to(GUDANG_DB)
        if any(part.startswith("_") for part in rel.parts[:-1]):
            continue

        module = path.stem
        if path.parent.name == "master":
            fallback_year = active_year
        else:
            match = re.search(r"_(19\d{2}|20\d{2})\.csv$", path.name)
            fallback_year = int(match.group(1)) if match else 0
            if match:
                module = module[:-5]

        is_corruption_module = "korup" in module.lower()

        for row in iter_csv_rows(path):
            total_rows += 1
            decision = publication_decision(row)
            if not decision.allowed:
                quarantined_rows += 1
                quarantine_reasons[decision.reason] += 1
                continue

            published_rows += 1
            year = row_year(row, fallback_year)
            month = row_month(row)
            lower = {str(k).strip().lower(): v for k, v in row.items()}
            loss = loss_amount(row)
            recovery = recovery_amount(row)

            if year in yearly_loss:
                yearly_loss[year] += loss

            has_case = any(lower.get(k) for k in ("kasus", "nama_kasus", "kasus_terkait"))
            has_actor = any(lower.get(k) for k in ("nama", "nama_pejabat", "pelaku"))

            if is_corruption_module and has_case:
                historical_cases += 1
                historical_cases_by_module[module] = historical_cases_by_module.get(module, 0) + 1
            if is_corruption_module and has_actor:
                historical_actors += 1

            in_active_period = year == active_year and month == active_month
            if is_corruption_module and in_active_period:
                active_loss += loss
                active_recovery += recovery
                active_cases += int(has_case)
                active_actors += int(has_actor)

    payload = {
        "tahun": active_year,
        "bulan": active_month,
        "bulan_nama": active["month_name"],
        "kerugian_total": round(active_loss),
        "recovery_total": round(active_recovery),
        "jumlah_kasus": active_cases,
        "jumlah_koruptor": active_actors,
        "jumlah_kasus_historis": historical_cases,
        "jumlah_koruptor_historis": historical_actors,
        "jumlah_kasus_historis_by_module": dict(sorted(historical_cases_by_module.items())),
        "history_akumulasi": {str(y): round(v) for y, v in sorted(yearly_loss.items())},
        "data_rows_terisi": published_rows,
        "publication_gate": {
            "mode": "DEFAULT_DENY_EVIDENCE_FIRST",
            "rows_scanned": total_rows,
            "rows_published": published_rows,
            "rows_quarantined": quarantined_rows,
            "quarantine_reasons": dict(sorted(quarantine_reasons.items())),
            "money_alias_policy": "FIRST_CANONICAL_ALIAS_ONLY_NO_DOUBLE_COUNT",
        },
        "catatan": (
            "Auto-generated hanya dari record yang lolos publication evidence gate. "
            "DRAFT/REVIEW/UNVERIFIED/CANDIDATE tidak boleh memengaruhi angka publik."
        ),
    }
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
