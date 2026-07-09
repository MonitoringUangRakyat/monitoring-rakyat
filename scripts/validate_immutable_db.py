from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
GUDANG_DB = ROOT / "gudang-db"
LEDGER = GUDANG_DB / "_ledger"
IMMUTABLE_INDEX = LEDGER / "immutable_index.json"

ID_COLUMNS = ("id", "record_id", "kode", "nomor_perkara")
PROTECTED_STATUS_RE = re.compile(r"\b(VERIFIED|INKRACHT|INKRACHT|INKRAH|INKRACHT)\b", re.IGNORECASE)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        return [row for row in reader if any((value or "").strip() for value in row.values())]


def norm_row(row: dict[str, str]) -> dict[str, str]:
    return {str(k or "").strip().lower(): str(v or "").strip() for k, v in row.items()}


def row_id(row: dict[str, str]) -> str:
    lower = norm_row(row)
    for key in ID_COLUMNS:
        if lower.get(key):
            return lower[key]
    return ""


def protected_status(row: dict[str, str]) -> str:
    lower = norm_row(row)
    status = " ".join(
        lower.get(key, "")
        for key in ("status", "status_verifikasi", "status_hukum", "vonis", "catatan_hukum")
    )
    return status if PROTECTED_STATUS_RE.search(status) else ""


def row_hash(row: dict[str, str]) -> str:
    payload = json.dumps(norm_row(row), ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def iter_protected_records() -> list[dict[str, str]]:
    records: list[dict[str, str]] = []
    for path in sorted(GUDANG_DB.rglob("*.csv")):
        if "_ledger" in path.parts:
            continue
        for row in read_csv(path):
            rid = row_id(row)
            status = protected_status(row)
            if not rid or not status:
                continue
            records.append(
                {
                    "record_id": rid,
                    "file_path": path.relative_to(ROOT).as_posix(),
                    "row_hash": row_hash(row),
                    "status_snapshot": status,
                }
            )
    return records


def write_index(records: list[dict[str, str]]) -> None:
    LEDGER.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema": "monitoring-rakyat.immutable-index.v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "policy": "VERIFIED/INKRACHT records must not be deleted. Use DISPUTED/RETRACTED with evidence instead.",
        "protected_count": len(records),
        "records": records,
    }
    IMMUTABLE_INDEX.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def validate_index() -> int:
    if not IMMUTABLE_INDEX.exists():
        print("IMMUTABLE_INDEX_MISSING: run scripts/validate_immutable_db.py --refresh")
        return 1

    payload = json.loads(IMMUTABLE_INDEX.read_text(encoding="utf-8"))
    indexed = payload.get("records") or []
    current_records = iter_protected_records()
    current_by_key = {(r["file_path"], r["record_id"]): r for r in current_records}

    missing: list[dict[str, str]] = []
    changed: list[tuple[dict[str, str], dict[str, str]]] = []
    for item in indexed:
        key = (item.get("file_path", ""), item.get("record_id", ""))
        current = current_by_key.get(key)
        if not current:
            missing.append(item)
            continue
        if current.get("row_hash") != item.get("row_hash"):
            changed.append((item, current))

    if missing:
        print("IMMUTABLE_DB_VALIDATION_FAILED")
        for item in missing:
            print(f"MISSING_PROTECTED_RECORD {item.get('file_path')} :: {item.get('record_id')} :: {item.get('status_snapshot')}")
        print("Action: create AUTO_RESTORE_VALID_DB PR or mark record DISPUTED/RETRACTED with evidence before removal.")
        return 1

    if changed:
        print("IMMUTABLE_DB_CONTENT_CHANGED")
        for old, new in changed[:100]:
            print(f"CHANGED_PROTECTED_RECORD {old.get('file_path')} :: {old.get('record_id')}")
        print("Note: changes are allowed only with review/evidence. Run --refresh after accepted correction.")

    print(f"IMMUTABLE_DB_OK protected_records={len(indexed)}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--refresh", action="store_true", help="Rebuild immutable index from current VERIFIED/INKRACHT records.")
    args = parser.parse_args()

    if args.refresh:
        records = iter_protected_records()
        write_index(records)
        print(f"Wrote {IMMUTABLE_INDEX.relative_to(ROOT)} with {len(records)} protected records.")
        return 0

    return validate_index()


if __name__ == "__main__":
    raise SystemExit(main())
