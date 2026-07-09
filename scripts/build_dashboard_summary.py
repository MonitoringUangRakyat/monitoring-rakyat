from __future__ import annotations

import csv
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
GUDANG_DB = ROOT / "gudang-db"
ACTIVE_PERIOD = ROOT / "dashboard" / "active-period.json"
OUT = ROOT / "dashboard" / "dashboard_summary.json"
MONEY_COLUMNS = {
    "kerugian",
    "nilai_kerugian",
    "kerugian_diakibatkan",
    "total_kerugian",
    "recovery",
    "dikembalikan",
    "dikembalikan_ke_negara",
    "asset_recovery",
}


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


def iter_csv_rows(path: Path):
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            if any((value or "").strip() for value in row.values()):
                yield row


def row_year(row: dict[str, str], fallback: int = 0) -> int:
    for key in ("tahun", "Tahun", "year", "tahun_data"):
        value = row.get(key)
        if value:
            match = re.search(r"(19\d{2}|20\d{2})", value)
            if match:
                return int(match.group(1))
    return fallback


def main() -> None:
    active = json.loads(ACTIVE_PERIOD.read_text(encoding="utf-8"))
    active_year = int(active["year"])
    trend_years = int(active.get("trend_years", 10))
    min_trend_year = active_year - trend_years + 1

    yearly_loss: dict[int, float] = {year: 0.0 for year in range(min_trend_year, active_year + 1)}
    active_loss = 0.0
    active_recovery = 0.0
    active_cases = 0
    active_actors = 0
    historical_cases = 0
    historical_actors = 0
    historical_cases_by_module: dict[str, int] = {}
    filled_rows = 0

    for path in sorted(GUDANG_DB.rglob("*.csv")):
      if any(part.startswith("_") for part in path.relative_to(GUDANG_DB).parts[:-1]):
          continue
      module = path.stem
      if path.parent.name == "master":
          fallback_year = active_year
      else:
          match = re.search(r"_(19\d{2}|20\d{2})\.csv$", path.name)
          fallback_year = int(match.group(1)) if match else 0
          if match:
              module = module[: -5]
      is_corruption_module = "korup" in module.lower()

      for row in iter_csv_rows(path):
          filled_rows += 1
          year = row_year(row, fallback_year)
          lower = {str(k).strip().lower(): v for k, v in row.items()}
          loss = sum(parse_money(lower.get(col)) for col in MONEY_COLUMNS if "recovery" not in col and "dikembalikan" not in col and col != "asset_recovery")
          recovery = (
              parse_money(lower.get("recovery"))
              + parse_money(lower.get("dikembalikan"))
              + parse_money(lower.get("dikembalikan_ke_negara"))
              + parse_money(lower.get("asset_recovery"))
          )

          if year in yearly_loss:
              yearly_loss[year] += loss
          has_case = any(lower.get(k) for k in ("kasus", "nama_kasus", "kasus_terkait"))
          has_actor = any(lower.get(k) for k in ("nama", "nama_pejabat", "pelaku"))
          if is_corruption_module and has_case:
              historical_cases += 1
              historical_cases_by_module[module] = historical_cases_by_module.get(module, 0) + 1
          if is_corruption_module and has_actor:
              historical_actors += 1
          if is_corruption_module and year == active_year:
              active_loss += loss
              active_recovery += recovery
              if has_case:
                  active_cases += 1
              if has_actor:
                  active_actors += 1

    payload = {
        "tahun": active_year,
        "bulan": active["month"],
        "bulan_nama": active["month_name"],
        "kerugian_total": round(active_loss),
        "recovery_total": round(active_recovery),
        "jumlah_kasus": active_cases,
        "jumlah_koruptor": active_actors,
        "jumlah_kasus_historis": historical_cases,
        "jumlah_koruptor_historis": historical_actors,
        "jumlah_kasus_historis_by_module": dict(sorted(historical_cases_by_module.items())),
        "history_akumulasi": {str(year): round(value) for year, value in sorted(yearly_loss.items())},
        "data_rows_terisi": filled_rows,
        "catatan": "Auto-generated dari Gudang DB. Jika nilai masih 0, CSV terkait masih berupa template/header atau belum memiliki kolom nominal terisi.",
    }

    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
