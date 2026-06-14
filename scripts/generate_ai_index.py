from __future__ import annotations

import csv
import json
import re
from collections import defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
GUDANG_DB = ROOT / "gudang-db"
OUT = GUDANG_DB / "_index" / "ai_index.json"
YEAR_FILE = re.compile(r"^(.+)_((?:19|20)\d{2})\.csv$", re.IGNORECASE)

ERA_RANGES = {
    "1_era_orba_1966_1998": [1966, 1998],
    "2_era_reformasi_1999_2010": [1999, 2010],
    "3_era_modern_2011_2026": [2011, 2026],
}


def read_header(path: Path) -> list[str]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.reader(handle)
        return next(reader, [])


def main() -> None:
    modules: dict[str, dict] = defaultdict(lambda: {"kolom": [], "years": {}})

    master_files = [
        path.relative_to(ROOT).as_posix()
        for path in sorted((GUDANG_DB / "master").glob("*.csv"))
    ]

    for path in sorted(GUDANG_DB.glob("*_era_*/*.csv")):
        match = YEAR_FILE.match(path.name)
        if not match:
            continue

        module, year = match.group(1), match.group(2)
        header = read_header(path)
        item = modules[module]
        if not item["kolom"] and header:
            item["kolom"] = header
        item["years"][year] = path.relative_to(ROOT).as_posix()

    payload = {
        "project": "Monitoring Rakyat - Gudang DB",
        "purpose": "Index untuk AI Pengawas agar tahu modul, tahun, dan lokasi file CSV.",
        "eras": {name: {"range": value} for name, value in ERA_RANGES.items()},
        "master_files": master_files,
        "modules": dict(sorted(modules.items())),
    }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {OUT.relative_to(ROOT)} with {len(modules)} modules.")


if __name__ == "__main__":
    main()
