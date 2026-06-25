from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "gudang-db" / "_sources" / "nemesis_integration.json"
DEFAULT_INTAKE = ROOT / "gudang-db" / "_intake" / "nemesis"
QUEUE_JSON = ROOT / "gudang-db" / "_queue" / "nemesis_procurement_candidates.json"
QUEUE_CSV = ROOT / "gudang-db" / "_queue" / "nemesis_procurement_candidates.csv"
STATUS_JSON = ROOT / "dashboard" / "nemesis_integration_status.json"
ACTIVE_PERIOD = ROOT / "dashboard" / "active-period.json"
MAX_ROWS_DEFAULT = 25000


def read_json(path: Path, fallback):
    if not path.exists():
        return fallback
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, payload) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def normalize_key(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", str(value or "").lower())


def flatten(value, prefix: str = "") -> dict[str, object]:
    out: dict[str, object] = {}
    if isinstance(value, dict):
        for key, item in value.items():
            child = f"{prefix}.{key}" if prefix else str(key)
            out.update(flatten(item, child))
    else:
        out[prefix] = value
    return out


def pick(row: dict, aliases: list[str]) -> str:
    flat = flatten(row)
    by_exact = {str(key): value for key, value in flat.items()}
    by_norm = {normalize_key(key): value for key, value in flat.items()}
    for alias in aliases:
        if alias in by_exact and by_exact[alias] not in (None, ""):
            return str(by_exact[alias]).strip()
        value = by_norm.get(normalize_key(alias))
        if value not in (None, ""):
            return str(value).strip()
    return ""


def parse_money(value: str | int | float | None) -> int:
    if value is None:
        return 0
    if isinstance(value, (int, float)):
        return round(float(value))
    text = str(value).strip().lower()
    if not text:
        return 0
    multiplier = 1
    if "triliun" in text or re.search(r"\bt\b", text):
        multiplier = 1_000_000_000_000
    elif "miliar" in text or re.search(r"\bm\b", text):
        multiplier = 1_000_000_000
    elif "juta" in text or "jt" in text:
        multiplier = 1_000_000
    match = re.search(r"-?\d[\d.,]*", text.replace("rp", "").replace("idr", ""))
    if not match:
        return 0
    raw = match.group(0)
    if "," in raw and re.search(r",\d{1,2}$", raw):
        raw = raw.replace(".", "").replace(",", ".")
    else:
        raw = raw.replace(".", "").replace(",", "")
    try:
        return round(float(raw) * multiplier)
    except ValueError:
        return 0


def parse_year(value: str, fallback: int) -> int:
    match = re.search(r"(19\d{2}|20\d{2})", str(value or ""))
    return int(match.group(1)) if match else fallback


def candidate_id(row: dict) -> str:
    raw = "|".join(
        str(row.get(key, ""))
        for key in ("package_id", "package_name", "agency", "satker", "budget")
    )
    return "MR-NEMESIS-" + hashlib.sha256(raw.encode("utf-8", "ignore")).hexdigest()[:16].upper()


def iter_input_files(path: Path) -> list[Path]:
    if path.is_file():
        return [path]
    if not path.exists():
        return []
    return [
        item
        for item in sorted(path.rglob("*"))
        if item.is_file() and item.suffix.lower() in {".jsonl", ".json", ".csv"}
    ]


def read_records(path: Path) -> list[dict]:
    suffix = path.suffix.lower()
    if suffix == ".jsonl":
        rows = []
        for line in path.read_text(encoding="utf-8-sig", errors="ignore").splitlines():
            if line.strip():
                rows.append(json.loads(line))
        return rows
    if suffix == ".json":
        payload = json.loads(path.read_text(encoding="utf-8-sig", errors="ignore"))
        if isinstance(payload, list):
            return [item for item in payload if isinstance(item, dict)]
        if isinstance(payload, dict):
            for key in ("data", "rows", "items", "records", "result"):
                if isinstance(payload.get(key), list):
                    return [item for item in payload[key] if isinstance(item, dict)]
            return [payload]
    if suffix == ".csv":
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            return [{str(k or "").strip(): str(v or "").strip() for k, v in row.items()} for row in csv.DictReader(handle)]
    return []


def target_modules(row: dict) -> list[str]:
    text = " ".join(str(row.get(key, "")) for key in ("agency", "satker", "package_name", "risk_reason")).lower()
    modules = ["redflag", "vendor"]
    if any(word in text for word in ("dprd", "dpr", "sekretariat dewan", "dewan perwakilan")):
        modules.append("prog_legislatif")
    elif any(word in text for word in ("kabupaten", "kota", "provinsi", "dinas", "pemda", "sekda")):
        modules.append("prog_daerah")
    else:
        modules.append("prog_eksekutif")
    return modules


def normalize_record(raw: dict, file_name: str, manifest: dict, fallback_year: int) -> dict:
    mapping = manifest["field_mapping"]
    package_id = pick(raw, mapping["package_id"])
    package_name = pick(raw, mapping["package_name"])
    agency = pick(raw, mapping["agency"])
    satker = pick(raw, mapping["satker"])
    location = pick(raw, mapping["location"])
    budget_text = pick(raw, mapping["budget"])
    waste_text = pick(raw, mapping["waste_potential"])
    row = {
        "package_id": package_id,
        "package_name": package_name,
        "agency": agency,
        "satker": satker,
        "location": location,
        "budget": parse_money(budget_text),
        "budget_raw": budget_text,
        "funding_source": pick(raw, mapping["funding_source"]),
        "waste_potential": parse_money(waste_text),
        "waste_potential_raw": waste_text,
        "risk_label": pick(raw, mapping["risk_label"]),
        "risk_reason": pick(raw, mapping["risk_reason"]),
        "year": parse_year(" ".join(str(value) for value in raw.values()), fallback_year),
        "source": "Nemesis",
        "source_url": manifest["source_url"],
        "source_file": file_name,
        "status": manifest["trust_policy"]["default_status"],
        "evidence_status": "NEEDS_LKPP_SIRUP_CROSSCHECK",
        "publish_guard": manifest["trust_policy"]["rule"],
    }
    row["target_modules"] = target_modules(row)
    row["id"] = candidate_id(row)
    return row


def write_queue(candidates: list[dict], generated_at: str, manifest: dict) -> None:
    payload = {
        "generated_at": generated_at,
        "source": manifest["name"],
        "source_class": manifest["trust_policy"]["source_class"],
        "allowed_as_final_evidence": False,
        "default_status": manifest["trust_policy"]["default_status"],
        "required_crosscheck": manifest["trust_policy"]["required_crosscheck"],
        "count": len(candidates),
        "candidates": candidates,
    }
    write_json(QUEUE_JSON, payload)
    QUEUE_CSV.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "id",
        "year",
        "package_id",
        "package_name",
        "agency",
        "satker",
        "location",
        "budget",
        "funding_source",
        "waste_potential",
        "risk_label",
        "risk_reason",
        "target_modules",
        "status",
        "evidence_status",
        "source_url",
        "source_file",
    ]
    with QUEUE_CSV.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for item in candidates:
            row = dict(item)
            row["target_modules"] = "|".join(item.get("target_modules", []))
            writer.writerow({field: row.get(field, "") for field in fields})


def main() -> int:
    parser = argparse.ArgumentParser(description="Import Nemesis procurement analysis into Monitoring Rakyat draft queue.")
    parser.add_argument("--input", default=str(DEFAULT_INTAKE), help="Nemesis JSONL/JSON/CSV file or intake folder.")
    parser.add_argument("--max-rows", type=int, default=MAX_ROWS_DEFAULT)
    args = parser.parse_args()

    manifest = read_json(MANIFEST, {})
    active = read_json(ACTIVE_PERIOD, {"year": datetime.now(ZoneInfo("Asia/Jakarta")).year})
    fallback_year = int(active.get("year") or 2026)
    now = datetime.now(ZoneInfo("Asia/Jakarta")).isoformat(timespec="seconds")
    input_path = Path(args.input)
    if not input_path.is_absolute():
        input_path = ROOT / input_path

    files = iter_input_files(input_path)
    candidates_by_id: dict[str, dict] = {}
    rows_seen = 0
    errors = []
    for file in files:
        try:
            records = read_records(file)
        except Exception as exc:
            errors.append({"file": str(file.relative_to(ROOT)), "error": str(exc)[:200]})
            continue
        for raw in records:
            rows_seen += 1
            if rows_seen > args.max_rows:
                break
            item = normalize_record(raw, file.relative_to(ROOT).as_posix(), manifest, fallback_year)
            if not item["package_name"] and not item["package_id"]:
                continue
            candidates_by_id[item["id"]] = item
        if rows_seen > args.max_rows:
            break

    candidates = sorted(candidates_by_id.values(), key=lambda item: (item["year"], item["agency"], item["package_name"]))
    write_queue(candidates, now, manifest)

    status = {
        "generated_at": now,
        "source": manifest.get("name", "Nemesis"),
        "source_url": manifest.get("source_url", ""),
        "repo_url": manifest.get("repo_url", ""),
        "transparency_url": manifest.get("transparency_url", ""),
        "intake_path": input_path.relative_to(ROOT).as_posix() if input_path.is_relative_to(ROOT) else str(input_path),
        "input_files": [file.relative_to(ROOT).as_posix() for file in files],
        "input_present": bool(files),
        "rows_seen": rows_seen,
        "candidates_written": len(candidates),
        "queue_json": QUEUE_JSON.relative_to(ROOT).as_posix(),
        "queue_csv": QUEUE_CSV.relative_to(ROOT).as_posix(),
        "default_status": manifest.get("trust_policy", {}).get("default_status", "DRAFT_REVIEW"),
        "allowed_as_final_evidence": False,
        "required_crosscheck": manifest.get("trust_policy", {}).get("required_crosscheck", []),
        "errors": errors,
    }
    write_json(STATUS_JSON, status)
    print(f"Nemesis intake files: {len(files)}")
    print(f"Nemesis candidates written: {len(candidates)}")
    print(f"Status: {STATUS_JSON.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
