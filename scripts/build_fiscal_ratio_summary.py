from __future__ import annotations

import csv
import json
import re
from collections import Counter
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from evidence_policy import first_money, publication_decision

ROOT = Path(__file__).resolve().parents[1]
GUDANG_DB = ROOT / "gudang-db"
ACTIVE_PERIOD = ROOT / "dashboard" / "active-period.json"
OUT = ROOT / "dashboard" / "fiscal_ratio_annual.json"
MIN_YEARS = 10


def read_rows(path: Path):
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return [{str(k or "").strip(): str(v or "").strip() for k, v in row.items()} for row in csv.DictReader(handle)]


def module_year_from_path(path: Path) -> tuple[str, int]:
    match = re.match(r"(.+)_((?:19|20)\d{2})\.csv$", path.name, re.IGNORECASE)
    return (match.group(1), int(match.group(2))) if match else (path.stem, 0)


def year_from_row(row: dict[str, str], fallback: int) -> int:
    for key in ("tahun", "Tahun", "year", "Tahun_Data"):
        value = row.get(key)
        if value:
            match = re.search(r"(19\d{2}|20\d{2})", str(value))
            if match:
                return int(match.group(1))
    return fallback


VALUE_COLUMNS = {
    "akuntansi": ("Debet_Rp", "Realisasi", "Belanja", "Pagu_APBN"),
    "pajak": ("Nilai", "Penerimaan", "Realisasi"),
    "sda": ("Nilai_Ekonomi", "Nilai", "PNBP", "Realisasi"),
    "korupsi": ("Kerugian", "Nilai_Kerugian", "Kerugian_Diakibatkan", "Total_Kerugian"),
}
TARGET_KEYS = {
    "akuntansi": "belanja_apbn",
    "pajak": "pendapatan_pajak",
    "sda": "hasil_sda",
    "korupsi": "kerugian_korupsi",
}


def main() -> None:
    active = json.loads(ACTIVE_PERIOD.read_text(encoding="utf-8"))
    end_year = int(active["year"])
    trend_years = max(MIN_YEARS, int(active.get("trend_years", MIN_YEARS)))
    start_year = end_year - trend_years + 1
    years = list(range(start_year, end_year + 1))

    by_year = {
        y: {
            "year": y,
            "belanja_apbn": 0.0,
            "pendapatan_pajak": 0.0,
            "hasil_sda": 0.0,
            "kerugian_korupsi": 0.0,
            "rows": {m: 0 for m in VALUE_COLUMNS},
            "quarantined_rows": 0,
            "quarantine_reasons": Counter(),
        }
        for y in years
    }

    for path in sorted(GUDANG_DB.rglob("*.csv")):
        rel = path.relative_to(GUDANG_DB)
        if any(part.startswith("_") for part in rel.parts[:-1]):
            continue
        module, file_year = module_year_from_path(path)
        if module not in VALUE_COLUMNS:
            continue

        for row in read_rows(path):
            if not any(str(v or "").strip() for v in row.values()):
                continue
            year = year_from_row(row, file_year)
            if year not in by_year:
                continue

            decision = publication_decision(row)
            if not decision.allowed:
                by_year[year]["quarantined_rows"] += 1
                by_year[year]["quarantine_reasons"][decision.reason] += 1
                continue

            value = first_money(row, VALUE_COLUMNS[module])
            if value:
                by_year[year][TARGET_KEYS[module]] += value
                by_year[year]["rows"][module] += 1

    data = []
    for year in years:
        row = by_year[year]
        belanja = row["belanja_apbn"]
        pajak = row["pendapatan_pajak"]
        sda = row["hasil_sda"]
        korupsi = row["kerugian_korupsi"]
        any_value = any((belanja, pajak, sda, korupsi))
        data.append({
            "year": year,
            "belanja_apbn": round(belanja),
            "pendapatan_pajak": round(pajak),
            "hasil_sda": round(sda),
            "kerugian_korupsi": round(korupsi),
            "belanja_apbn_t": round(belanja / 1e12, 3),
            "pendapatan_pajak_t": round(pajak / 1e12, 3),
            "hasil_sda_t": round(sda / 1e12, 3),
            "kerugian_korupsi_t": round(korupsi / 1e12, 3),
            "korupsi_vs_belanja_pct": round(korupsi / belanja * 100, 3) if belanja else 0,
            "korupsi_vs_pajak_pct": round(korupsi / pajak * 100, 3) if pajak else 0,
            "status": "HAS_VERIFIED_DB_VALUE" if any_value else "KOSONG_MENUNGGU_VERIFIKASI",
            "source_rows": row["rows"],
            "quarantined_rows": row["quarantined_rows"],
            "quarantine_reasons": dict(row["quarantine_reasons"]),
        })

    payload = {
        "generated_at": datetime.now(ZoneInfo("Asia/Jakarta")).isoformat(timespec="seconds"),
        "source": "Gudang DB CSV yearly aggregation - verified/publication-gated only",
        "policy": "DRAFT/REVIEW/UNVERIFIED/CANDIDATE excluded from public fiscal ratios.",
        "minimum_years": MIN_YEARS,
        "trend_years": trend_years,
        "year_range": [start_year, end_year],
        "units": "IDR and Rp triliun",
        "publication_gate": "DEFAULT_DENY_EVIDENCE_FIRST",
        "data": data,
    }
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {OUT.relative_to(ROOT)} with {len(data)} annual rows.")


if __name__ == "__main__":
    main()
