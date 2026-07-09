from __future__ import annotations

import csv
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
GUDANG_DB = ROOT / "gudang-db"
YEAR_FILE = re.compile(r"^(.+)_((?:19|20)\d{2})\.csv$", re.IGNORECASE)


def read_header(path: Path) -> list[str]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.reader(handle)
        return next(reader, [])


def main() -> int:
    errors: list[str] = []
    warnings: list[str] = []
    csv_files = sorted(
        path
        for path in GUDANG_DB.rglob("*.csv")
        if not any(part.startswith("_") for part in path.relative_to(GUDANG_DB).parts[:-1])
    )

    if not csv_files:
        errors.append("No CSV files found under gudang-db/")

    for path in csv_files:
        rel = path.relative_to(ROOT).as_posix()
        try:
            header = read_header(path)
        except UnicodeDecodeError:
            errors.append(f"{rel}: file is not valid UTF-8")
            continue
        except Exception as exc:
            errors.append(f"{rel}: cannot read CSV ({exc})")
            continue

        if not header:
            errors.append(f"{rel}: missing header")
            continue

        if path.parent.name != "master":
            match = YEAR_FILE.match(path.name)
            if not match:
                errors.append(f"{rel}: expected file name {{modul}}_{{tahun}}.csv")
            elif "tahun" not in [h.strip().lower() for h in header]:
                warnings.append(f"{rel}: header does not include tahun")

        duplicate_headers = sorted({h for h in header if header.count(h) > 1 and h})
        if duplicate_headers:
            warnings.append(f"{rel}: duplicate columns: {', '.join(duplicate_headers)}")

    print(f"CSV checked: {len(csv_files)}")
    print(f"Errors: {len(errors)}")
    print(f"Warnings: {len(warnings)}")

    for item in errors[:50]:
        print(f"ERROR: {item}")
    for item in warnings[:50]:
        print(f"WARN: {item}")

    if len(errors) > 50:
        print(f"... {len(errors) - 50} more errors")
    if len(warnings) > 50:
        print(f"... {len(warnings) - 50} more warnings")

    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
