from __future__ import annotations

import csv
import json
import re
from pathlib import Path
from zoneinfo import ZoneInfo
from datetime import datetime


ROOT = Path(__file__).resolve().parents[1]
GUDANG_DB = ROOT / "gudang-db"
ACTIVE_PERIOD = ROOT / "dashboard" / "active-period.json"
OUT = ROOT / "dashboard" / "fiscal_ratio_annual.json"
MIN_YEARS = 10


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return [{str(k or "").strip(): str(v or "").strip() for k, v in row.items()} for row in csv.DictReader(handle)]


def parse_money(value: str | int | float | None) -> float:
    if value is None:
        return 0.0
    if isinstance(value, (int, float)):
        return float(value)
    text = str(value).strip().lower()
    if not text:
        return 0.0
    multiplier = 1
    if "triliun" in text or re.search(r"\bt\b", text):
        multiplier = 1_000_000_000_000
    elif "miliar" in text or re.search(r"\bm\b", text):
        multiplier = 1_000_000_000
    elif "juta" in text or "jt" in text:
        multiplier = 1_000_000
    match = re.search(r"-?\d[\d.,]*", text.replace("rp", "").replace("idr", ""))
    if not match:
        return 0.0
    raw = match.group(0)
    if "," in raw and re.search(r",\d{1,2}$", raw):
        raw = raw.replace(".", "").replace(",", ".")
    else:
        raw = raw.replace(".", "").replace(",", "")
    try:
        return float(raw) * multiplier
    except ValueError:
        return 0.0


def module_year_from_path(path: Path) -> tuple[str, int]:
    match = re.match(r"(.+)_((?:19|20)\d{2})\.csv$", path.name, re.IGNORECASE)
    if not match:
        return path.stem, 0
    return match.group(1), int(match.group(2))


def year_from_row(row: dict[str, str], fallback: int) -> int:
    for key in ("tahun", "Tahun", "year", "Tahun_Data"):
        value = row.get(key)
        if value:
            match = re.search(r"(19\d{2}|20\d{2})", str(value))
            if match:
                return int(match.group(1))
    return fallback


def first_money(row: dict[str, str], columns: tuple[str, ...]) -> float:
    lower = {str(k).strip().lower(): v for k, v in row.items()}
    for column in columns:
        value = lower.get(column.lower())
        if value is not None and str(value).strip():
            return parse_money(value)
    return 0.0


def main() -> None:
    active = read_json(ACTIVE_PERIOD)
    end_year = int(active["year"])
    trend_years = max(MIN_YEARS, int(active.get("trend_years", MIN_YEARS)))
    start_year = end_year - trend_years + 1
    years = list(range(start_year, end_year + 1))
    by_year = {
        year: {
            "year": year,
            "belanja_apbn": 0,
            "pendapatan_pajak": 0,
            "hasil_sda": 0,
            "kerugian_korupsi": 0,
            "rows": {"akuntansi": 0, "pajak": 0, "sda": 0, "korupsi": 0},
        }
        for year in years
    }

    for path in sorted(GUDANG_DB.rglob("*.csv")):
        if any(part.startswith("_") for part in path.relative_to(GUDANG_DB).parts[:-1]):
            continue
        module, file_year = module_year_from_path(path)
        if module not in {"akuntansi", "pajak", "sda", "korupsi"}:
            continue
        for row in read_rows(path):
            if not any(str(value or "").strip() for value in row.values()):
                continue
            year = year_from_row(row, file_year)
            if year not in by_year:
                continue
            if module == "akuntansi":
                value = first_money(row, ("Debet_Rp", "Realisasi", "Belanja", "Pagu_APBN"))
                by_year[year]["belanja_apbn"] += value
                if value:
                    by_year[year]["rows"]["akuntansi"] += 1
            elif module == "pajak":
                value = first_money(row, ("Nilai", "Penerimaan", "Realisasi"))
                by_year[year]["pendapatan_pajak"] += value
                if value:
                    by_year[year]["rows"]["pajak"] += 1
            elif module == "sda":
                value = first_money(row, ("Nilai_Ekonomi", "Nilai", "PNBP", "Realisasi"))
                by_year[year]["hasil_sda"] += value
                if value:
                    by_year[year]["rows"]["sda"] += 1
            elif module == "korupsi":
                value = first_money(row, ("Kerugian", "Nilai_Kerugian", "Kerugian_Diakibatkan", "Total_Kerugian"))
                by_year[year]["kerugian_korupsi"] += value
                if value:
                    by_year[year]["rows"]["korupsi"] += 1

    data = []
    for year in years:
        row = by_year[year]
        belanja = row["belanja_apbn"]
        pajak = row["pendapatan_pajak"]
        sda = row["hasil_sda"]
        korupsi = row["kerugian_korupsi"]
        data.append(
            {
                "year": year,
                "belanja_apbn": round(belanja),
                "pendapatan_pajak": round(pajak),
                "hasil_sda": round(sda),
                "kerugian_korupsi": round(korupsi),
                "belanja_apbn_t": round(belanja / 1_000_000_000_000, 3),
                "pendapatan_pajak_t": round(pajak / 1_000_000_000_000, 3),
                "hasil_sda_t": round(sda / 1_000_000_000_000, 3),
                "kerugian_korupsi_t": round(korupsi / 1_000_000_000_000, 3),
                "korupsi_vs_belanja_pct": round((korupsi / belanja * 100), 3) if belanja else 0,
                "korupsi_vs_pajak_pct": round((korupsi / pajak * 100), 3) if pajak else 0,
                "status": "HAS_DB_VALUE" if any((belanja, pajak, sda, korupsi)) else "KOSONG_MENUNGGU_GUDANG_DB",
                "source_rows": row["rows"],
            }
        )

    payload = {
        "generated_at": datetime.now(ZoneInfo("Asia/Jakarta")).isoformat(timespec="seconds"),
        "source": "Gudang DB CSV yearly aggregation",
        "policy": "Grafik dashboard boleh menampilkan minimum 10 tahun karena hanya agregasi tahunan, bukan detail bulanan/harian.",
        "minimum_years": MIN_YEARS,
        "trend_years": trend_years,
        "year_range": [start_year, end_year],
        "units": "IDR and Rp triliun",
        "sync_contract": "Setiap update Gudang DB menjalankan script ini via release_check/GitHub Actions agar grafik otomatis sinkron.",
        "data": data,
    }
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {OUT.relative_to(ROOT)} with {len(data)} annual rows.")


if __name__ == "__main__":
    main()
