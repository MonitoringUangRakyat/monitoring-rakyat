from __future__ import annotations

import csv
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "gudang-db" / "3_era_modern_2011_2026"

# Rp triliun. Baseline ringkas agar grafik dashboard tahunan tidak kosong.
# Status tetap BASELINE_REVIEW: wajib dicross-check berkala ke BPS/Kemenkeu APBN KiTa/Nota Keuangan.
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


def rupiah_trillion(value: float) -> str:
    return str(round(value * 1_000_000_000_000))


def read_rows(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        return list(reader.fieldnames or []), [dict(row) for row in reader]


def write_rows(path: Path, fields: list[str], rows: list[dict[str, str]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def upsert(path: Path, row: dict[str, str], key: str = "col") -> bool:
    fields, rows = read_rows(path)
    if not fields:
        raise ValueError(f"{path} has no header")
    row = {field: row.get(field, "") for field in fields}
    existing = next((item for item in rows if item.get(key) == row.get(key)), None)
    if existing:
        existing.update(row)
        added = False
    else:
        rows.append(row)
        added = True
    write_rows(path, fields, rows)
    return added


def main() -> int:
    added = 0
    updated = 0
    for year, values in BASELINE.items():
        akuntansi = {
            "tahun": str(year),
            "col": f"BASELINE-FISCAL-AKUNTANSI-{year}",
            "Tanggal": f"{year}-12-31",
            "Bulan": "12",
            "Tahun": str(year),
            "Sektor": "Belanja Negara",
            "Keterangan": f"Baseline agregat tahunan Belanja APBN {year}",
            "Debet_Rp": rupiah_trillion(values["belanja_apbn"]),
            "Dokumen": SOURCE_NOTE,
            "Status": "BASELINE_REVIEW",
            "Aksi": "AUTO_SEED_FISCAL_BASELINE",
            "Sektor_Program": "APBN",
            "Pagu_APBN": rupiah_trillion(values["belanja_apbn"]),
            "Realisasi": rupiah_trillion(values["belanja_apbn"]),
        }
        pajak = {
            "tahun": str(year),
            "col": f"BASELINE-FISCAL-PAJAK-{year}",
            "Jenis_Pajak": "Penerimaan Perpajakan",
            "Objek_Sasaran": f"Baseline agregat tahunan penerimaan pajak {year}; {SOURCE_NOTE}",
            "Tahun": str(year),
            "Bulan": "12",
            "Nilai": rupiah_trillion(values["pendapatan_pajak"]),
            "Aksi": "BASELINE_REVIEW",
        }
        sda = {
            "tahun": str(year),
            "col": f"BASELINE-FISCAL-SDA-{year}",
            "Sektor": "PNBP Sumber Daya Alam",
            "Komoditas_Sumber": "Agregat SDA",
            "Keterangan": f"Baseline agregat tahunan hasil SDA {year}; {SOURCE_NOTE}",
            "Tahun": str(year),
            "Bulan": "12",
            "Nilai_Ekonomi": rupiah_trillion(values["hasil_sda"]),
            "Aksi": "BASELINE_REVIEW",
        }
        for module, row in (("akuntansi", akuntansi), ("pajak", pajak), ("sda", sda)):
            path = DB / f"{module}_{year}.csv"
            if upsert(path, row):
                added += 1
            else:
                updated += 1
    print(f"Fiscal baseline rows added={added} updated={updated}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
