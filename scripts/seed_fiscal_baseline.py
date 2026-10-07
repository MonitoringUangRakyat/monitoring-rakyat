from __future__ import annotations

import csv
import json
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "gudang-db" / "_baseline"
OUT = OUT_DIR / "fiscal_baseline_review.csv"
STATUS = ROOT / "dashboard" / "fiscal_baseline_review_status.json"

# Reviewer reference only. These values are not canonical facts and may not populate public modules.
BASELINE = {
    2015: {"belanja_apbn": 1806.5, "pendapatan_pajak": 1060.8, "hasil_sda": 100.9},
    2016: {"belanja_apbn": 1864.3, "pendapatan_pajak": 1105.8, "hasil_sda": 64.9},
    2017: {"belanja_apbn": 2007.4, "pendapatan_pajak": 1343.5, "hasil_sda": 111.1},
    2018: {"belanja_apbn": 2213.1, "pendapatan_pajak": 1518.8, "hasil_sda": 180.6},
    2019: {"belanja_apbn": 2309.3, "pendapatan_pajak": 1546.1, "hasil_sda": 154.9},
    2020: {"belanja_apbn": 2589.9, "pendapatan_pajak": 1285.1, "hasil_sda": 97.2},
    2021: {"belanja_apbn": 2786.4, "pendapatan_pajak": 1547.8, "hasil_sda": 149.5},
    2022: {"belanja_apbn": 3096.3, "pendapatan_pajak": 2034.6, "hasil_sda": 268.8},
    2023: {"belanja_apbn": 3121.9, "pendapatan_pajak": 2155.4, "hasil_sda": 223.3},
    2024: {"belanja_apbn": 3350.3, "pendapatan_pajak": 2309.9, "hasil_sda": 204.9},
    2025: {"belanja_apbn": 3621.3, "pendapatan_pajak": 2490.9, "hasil_sda": 217.3},
}
SOURCE_NOTE = "BASELINE_REVIEW_BPS_KEMENKEU_APBN_KITA_NOTA_KEUANGAN"

def idr(trillion: float) -> int:
    return round(trillion * 1_000_000_000_000)

def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    fields = ["year", "metric", "value_idr", "source_note", "verification_status", "public_allowed"]
    rows = []
    for year, metrics in BASELINE.items():
        for metric, value in metrics.items():
            rows.append({
                "year": year,
                "metric": metric,
                "value_idr": idr(value),
                "source_note": SOURCE_NOTE,
                "verification_status": "BASELINE_REVIEW",
                "public_allowed": "false",
            })
    with OUT.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    status = {
        "generated_at": datetime.now(ZoneInfo("Asia/Jakarta")).isoformat(timespec="seconds"),
        "rows": len(rows),
        "location": str(OUT.relative_to(ROOT)),
        "verification_status": "BASELINE_REVIEW",
        "public_allowed": False,
        "rule": "Review-only fiscal baselines never populate canonical module CSVs; official evidence is required for promotion.",
    }
    STATUS.write_text(json.dumps(status, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote review-only fiscal baseline rows={len(rows)}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
