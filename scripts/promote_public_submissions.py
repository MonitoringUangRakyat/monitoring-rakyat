from __future__ import annotations

import csv
import hashlib
import json
import re
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo


ROOT = Path(__file__).resolve().parents[1]
QUEUE_JSON = ROOT / "gudang-db" / "_queue" / "public_submissions.json"
INTAKE_CSV = ROOT / "gudang-db" / "_intake" / "public_submissions.csv"
STATUS_JSON = ROOT / "dashboard" / "public_submission_status.json"
MODERN_DIR = ROOT / "gudang-db" / "3_era_modern_2011_2026"

INTAKE_FIELDS = [
    "id",
    "issue_number",
    "title",
    "issue_url",
    "module",
    "year",
    "validity_score",
    "status",
    "promoted_at",
    "body_preview",
]


def now_jakarta() -> str:
    return datetime.now(ZoneInfo("Asia/Jakarta")).isoformat(timespec="seconds")


def read_json(path: Path) -> dict:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return [{str(k or ""): str(v or "") for k, v in row.items()} for row in csv.DictReader(handle)]


def read_csv_header(path: Path) -> list[str]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.reader(handle)
        return [str(item or "") for item in next(reader, [])]


def write_csv(path: Path, rows: list[dict[str, str]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def append_unique_csv(path: Path, new_rows: list[dict[str, str]], key_fields: tuple[str, ...]) -> int:
    if not new_rows:
        return 0
    existing = read_csv(path)
    fields = list(existing[0].keys()) if existing else list(new_rows[0].keys())
    for row in new_rows:
        for field in row:
            if field not in fields:
                fields.append(field)
    seen = {"|".join(row.get(field, "") for field in key_fields) for row in existing}
    added = 0
    for row in new_rows:
        key = "|".join(row.get(field, "") for field in key_fields)
        if key in seen:
            continue
        existing.append(row)
        seen.add(key)
        added += 1
    write_csv(path, existing, fields)
    return added


def detect_year(text: str, fallback: str = "") -> str:
    years = re.findall(r"(19\d{2}|20\d{2})", text or "")
    if not years:
        return fallback or ""
    return years[-1]


def parse_markdown_tables(text: str) -> list[list[str]]:
    rows: list[list[str]] = []
    for line in (text or "").splitlines():
        stripped = line.strip()
        if not stripped.startswith("|") or not stripped.endswith("|"):
            continue
        cells = [cell.strip().strip("*") for cell in stripped.strip("|").split("|")]
        if not cells or all(re.fullmatch(r":?-{2,}:?", cell or "") for cell in cells):
            continue
        rows.append(cells)
    return rows


def normalize_money(text: str) -> str:
    cleaned = re.sub(r"\*\*", "", text or "").strip()
    cleaned = re.sub(r"\s+", " ", cleaned)
    return cleaned


def stable_id(*parts: str) -> str:
    raw = "|".join(parts)
    return hashlib.sha256(raw.encode("utf-8", "ignore")).hexdigest()[:16].upper()


def anonymous_ref(candidate: dict[str, str]) -> str:
    ref = str(candidate.get("source_ref") or candidate.get("issue_url") or "")
    if ref.startswith("ANON_PUBLIC_SUBMISSION:"):
        return ref
    return f"ANON_PUBLIC_SUBMISSION:{candidate.get('id', 'UNKNOWN')}"


def korupsi_rows_from_candidate(candidate: dict[str, str]) -> list[dict[str, str]]:
    body = candidate.get("body_preview", "")
    source_ref = anonymous_ref(candidate)
    issue_id = candidate.get("id", "")
    table_rows = parse_markdown_tables(body)
    result: list[dict[str, str]] = []
    headers: list[str] = []
    for cells in table_rows:
        joined = " ".join(cells).lower()
        if {"nama kasus", "kerugian negara"}.issubset(set(joined.split())) or ("nama kasus" in joined and "kerugian" in joined):
            headers = [cell.lower() for cell in cells]
            continue
        if not headers or len(cells) < len(headers):
            continue
        mapped = dict(zip(headers, cells))
        case_name = mapped.get("nama kasus", "") or mapped.get("nama kasus / sektor", "")
        loss = mapped.get("kerugian negara", "") or mapped.get("estimasi kerugian negara", "")
        if not case_name or not loss:
            continue
        period = mapped.get("periode", "")
        year = detect_year(period, candidate.get("year", ""))
        if not year:
            year = detect_year(body, "2026")
        row_id = "PUB-KOR-" + stable_id(issue_id, case_name, year)
        result.append(
            {
                "tahun": year,
                "col": row_id,
                "Nama_Kasus": re.sub(r"\*\*", "", case_name).strip(),
                "Tahun": year,
                "Status_Hukum": "DRAFT_PUBLIC_SUBMISSION_NEEDS_AI_AUDIT",
                "Nama": re.sub(r"\*\*", "", mapped.get("terpidana utama", "")).strip(),
                "Kasus": re.sub(r"\*\*", "", case_name).strip(),
                "Nilai_Kerugian": normalize_money(loss),
                "Kerugian": normalize_money(loss),
                "Sumber_Perhitungan": "PUBLIC_SUBMISSION_NEEDS_SOURCE_CHECK",
                "Status_Verifikasi": "DRAFT_PUBLIC_SUBMISSION_READY_FOR_AUDIT_QUEUE",
                "Dikembalikan_ke_Negara": "",
                "Recovery_Rate": "",
                "Sumber_Temuan": "PUBLIC_SUBMISSION",
                "Ringkasan_Temuan": f"Masuk dari kontribusi publik anonim {issue_id}. Wajib cek sumber resmi sebelum final.",
                "Status_Tindak_Lanjut": "AI_AUDIT_REQUIRED",
                "Link_Referensi": source_ref,
            }
        )
    if result:
        return result
    if candidate.get("module") == "korupsi" and int(candidate.get("validity_score") or 0) >= 50:
        year = candidate.get("year") or detect_year(body, "2026")
        row_id = "PUB-KOR-" + stable_id(issue_id, candidate.get("title", ""), year)
        return [
            {
                "tahun": year,
                "col": row_id,
                "Nama_Kasus": candidate.get("title", "Kontribusi publik"),
                "Tahun": year,
                "Status_Hukum": "DRAFT_PUBLIC_SUBMISSION_NEEDS_AI_AUDIT",
                "Kasus": candidate.get("title", "Kontribusi publik"),
                "Nilai_Kerugian": "",
                "Kerugian": "",
                "Sumber_Perhitungan": "PUBLIC_SUBMISSION_NEEDS_SOURCE_CHECK",
                "Status_Verifikasi": "DRAFT_PUBLIC_SUBMISSION_READY_FOR_AUDIT_QUEUE",
                "Sumber_Temuan": "PUBLIC_SUBMISSION",
                "Ringkasan_Temuan": body[:500],
                "Status_Tindak_Lanjut": "AI_AUDIT_REQUIRED",
                "Link_Referensi": source_ref,
            }
        ]
    return []


def append_korupsi_rows(rows: list[dict[str, str]]) -> int:
    added = 0
    grouped: dict[str, list[dict[str, str]]] = {}
    for row in rows:
        year = detect_year(row.get("Tahun", "") or row.get("tahun", ""), "2026")
        grouped.setdefault(year, []).append(row)
    for year, items in grouped.items():
        path = MODERN_DIR / f"korupsi_{year}.csv"
        if not path.exists():
            continue
        existing_fields = read_csv_header(path)
        normalized = []
        for item in items:
            normalized.append({field: item.get(field, "") for field in existing_fields})
        added += append_unique_csv(path, normalized, ("col", "Nama_Kasus", "Tahun"))
    return added


def main() -> int:
    generated_at = now_jakarta()
    queue = read_json(QUEUE_JSON)
    candidates = queue.get("candidates") if isinstance(queue, dict) else []
    if not isinstance(candidates, list):
        candidates = []

    ready = [
        item
        for item in candidates
        if isinstance(item, dict)
        and int(item.get("validity_score") or 0) >= 50
        and str(item.get("status", "")).startswith("DRAFT_PUBLIC_SUBMISSION")
    ]

    intake_rows = [
        {
            "id": item.get("id", ""),
            "issue_number": str(item.get("issue_number", "")),
            "title": item.get("title", ""),
            "issue_url": item.get("issue_url", ""),
            "module": item.get("module", ""),
            "year": item.get("year", ""),
            "validity_score": str(item.get("validity_score", "")),
            "status": item.get("status", ""),
            "promoted_at": generated_at,
            "body_preview": item.get("body_preview", ""),
        }
        for item in ready
    ]
    intake_added = append_unique_csv(INTAKE_CSV, intake_rows, ("id",))

    korupsi_rows: list[dict[str, str]] = []
    for item in ready:
        korupsi_rows.extend(korupsi_rows_from_candidate(item))
    korupsi_added = append_korupsi_rows(korupsi_rows)

    status = read_json(STATUS_JSON)
    if not isinstance(status, dict):
        status = {}
    status.update(
        {
            "promoted_at": generated_at,
            "public_submissions_ready_for_audit": len(ready),
            "public_submissions_promoted_to_intake": intake_added,
            "public_korupsi_rows_mapped": len(korupsi_rows),
            "public_korupsi_rows_promoted": korupsi_added,
            "promotion_rule": ">=50 validity score masuk intake publik dan mapping CSV Gudang DB draft; final tetap wajib audit sumber.",
        }
    )
    STATUS_JSON.write_text(json.dumps(status, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Ready submissions: {len(ready)}")
    print(f"Promoted intake rows: {intake_added}")
    print(f"Promoted korupsi rows: {korupsi_added}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
