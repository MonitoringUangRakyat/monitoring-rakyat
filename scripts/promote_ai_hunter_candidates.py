from __future__ import annotations

import csv
import hashlib
import json
import re
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo


ROOT = Path(__file__).resolve().parents[1]
MODERN_DIR = ROOT / "gudang-db" / "3_era_modern_2011_2026"
QUEUE_DIR = ROOT / "gudang-db" / "_queue"
AI_QUEUE = QUEUE_DIR / "ai_pengawas_candidates.json"
NEMESIS_QUEUE = QUEUE_DIR / "nemesis_procurement_candidates.json"
PUBLIC_QUEUE = QUEUE_DIR / "public_submissions.json"
STATUS_JSON = ROOT / "dashboard" / "ai_hunter_promotion_status.json"
ACTIVE_PERIOD = ROOT / "dashboard" / "active-period.json"

MODULE_TARGETS = {
    "korupsi",
    "redflag",
    "vendor",
    "audit",
    "audittrail",
    "bea_cukai",
    "bumn",
    "pajak",
    "sda",
    "prog_daerah",
    "prog_eksekutif",
    "prog_legislatif",
    "parpol",
    "risknas",
}


def now_jakarta() -> str:
    return datetime.now(ZoneInfo("Asia/Jakarta")).isoformat(timespec="seconds")


def read_json(path: Path, fallback):
    if not path.exists():
        return fallback
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except Exception:
        return fallback


def read_rows(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    if not path.exists():
        return [], []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        fields = [str(field or "") for field in (reader.fieldnames or [])]
        rows = [{str(k or ""): str(v or "") for k, v in row.items()} for row in reader]
    return fields, rows


def write_rows(path: Path, fields: list[str], rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def stable_id(*parts: object) -> str:
    raw = "|".join(str(part or "") for part in parts)
    return hashlib.sha256(raw.encode("utf-8", "ignore")).hexdigest()[:16].upper()


def detect_year(*values: object, fallback: int = 2026) -> int:
    for value in values:
        match = re.search(r"(19\d{2}|20\d{2})", str(value or ""))
        if match:
            return int(match.group(1))
    return fallback


def parse_money(value: object) -> int:
    text = str(value or "").lower()
    if not text:
        return 0
    has_money_context = bool(
        re.search(
            r"\b(rp|idr|uang|suap|kerugian|kontrak|anggaran|pagu|realisasi|penerimaan|nilai|aset|disita|denda)\b",
            text,
        )
    )
    if not has_money_context:
        return 0
    multiplier = 1
    if "triliun" in text or re.search(r"\bt\b", text):
        multiplier = 1_000_000_000_000
    elif "miliar" in text or re.search(r"\bm\b", text):
        multiplier = 1_000_000_000
    elif "juta" in text or "jt" in text:
        multiplier = 1_000_000
    match = re.search(r"\d[\d.,]*", text.replace("rp", "").replace("idr", ""))
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


def money_label(value: int) -> str:
    if value <= 0:
        return ""
    return f"Rp {value:,}".replace(",", ".")


def compact_text(*values: object, limit: int = 650) -> str:
    text = " ".join(str(value or "") for value in values)
    text = re.sub(r"\s+", " ", text).strip()
    return text[:limit]


def risk_level(confidence: int) -> str:
    if confidence >= 85:
        return "HIGH"
    if confidence >= 70:
        return "MEDIUM"
    return "LOW"


def upsert_rows(path: Path, new_rows: list[dict[str, str]], key_field: str = "col") -> int:
    if not new_rows:
        return 0
    fields, rows = read_rows(path)
    if not fields:
        fields = list(new_rows[0].keys())
    for row in new_rows:
        for field in row:
            if field not in fields:
                fields.append(field)
    if key_field in fields:
        collapsed: dict[str, dict[str, str]] = {}
        no_key_rows: list[dict[str, str]] = []
        for row in rows:
            key = row.get(key_field, "")
            if key:
                collapsed[key] = row
            else:
                no_key_rows.append(row)
        rows = no_key_rows + list(collapsed.values())
    by_key = {row.get(key_field, ""): index for index, row in enumerate(rows) if row.get(key_field, "")}
    added = 0
    for row in new_rows:
        key = row.get(key_field, "")
        if key and key in by_key:
            rows[by_key[key]].update(row)
            continue
        rows.append(row)
        if key:
            by_key[key] = len(rows) - 1
        added += 1
    write_rows(path, fields, rows)
    return added


def active_year() -> int:
    active = read_json(ACTIVE_PERIOD, {})
    return int(active.get("year") or 2026)


def normalize_ai_candidates(fallback_year: int) -> list[dict]:
    payload = read_json(AI_QUEUE, {"candidates": []})
    out = []
    for item in payload.get("candidates", []):
        if not isinstance(item, dict):
            continue
        confidence = int(item.get("confidence") or 0)
        if confidence < 62:
            continue
        title = item.get("title", "")
        summary = item.get("summary", "")
        year = detect_year(item.get("year"), item.get("published"), title, summary, fallback=fallback_year)
        out.append(
            {
                "id": item.get("id") or "MR-AI-" + stable_id(title, item.get("link", "")),
                "source_type": "AI_HUNTER_RSS",
                "module": str(item.get("module") or "ai_pengawas"),
                "year": year,
                "month": str(item.get("month") or "0"),
                "title": title,
                "summary": summary,
                "link": item.get("link", ""),
                "source": item.get("source", ""),
                "confidence": confidence,
                "status": item.get("status") or "DRAFT_REVIEW",
                "task_type": item.get("task_type") or "",
            }
        )
    return out


def normalize_public_submissions(fallback_year: int) -> list[dict]:
    payload = read_json(PUBLIC_QUEUE, {"candidates": []})
    out = []
    for item in payload.get("candidates", []):
        if not isinstance(item, dict):
            continue
        score = int(item.get("validity_score") or 0)
        body = item.get("body_preview", "")
        title = item.get("title", "")
        year = detect_year(item.get("year"), title, body, fallback=fallback_year)
        ref = str(item.get("source_ref") or item.get("issue_url") or "")
        if not ref.startswith("ANON_PUBLIC_SUBMISSION:"):
            ref = f"ANON_PUBLIC_SUBMISSION:{item.get('id') or stable_id(title, body)}"
        out.append(
            {
                "id": item.get("id") or "MR-PUBLIC-" + stable_id(title, body),
                "source_type": "PUBLIC_SUBMISSION",
                "module": item.get("module") or "public_submission",
                "year": year,
                "month": "0",
                "title": title or "Kontribusi publik",
                "summary": body,
                "link": ref,
                "source": "Public Upload Anonim",
                "confidence": score,
                "status": item.get("status") or "DRAFT_PUBLIC_SUBMISSION",
                "task_type": "PUBLIC_UPLOAD_AUDIT",
            }
        )
    return out


def normalize_nemesis_candidates(fallback_year: int) -> list[dict]:
    payload = read_json(NEMESIS_QUEUE, {"candidates": []})
    out = []
    for item in payload.get("candidates", []):
        if not isinstance(item, dict):
            continue
        year = detect_year(item.get("year"), item.get("package_name"), fallback=fallback_year)
        budget = int(item.get("budget") or 0)
        waste = int(item.get("waste_potential") or 0)
        title = item.get("package_name") or item.get("package_id") or "Nemesis procurement signal"
        out.append(
            {
                "id": item.get("id") or "MR-NEMESIS-" + stable_id(title, item.get("agency", "")),
                "source_type": "NEMESIS_PROCUREMENT",
                "module": "redflag",
                "year": year,
                "month": "0",
                "title": title,
                "summary": compact_text(item.get("agency"), item.get("satker"), item.get("risk_label"), item.get("risk_reason"), money_label(budget), money_label(waste)),
                "link": item.get("source_url", ""),
                "source": "Nemesis",
                "confidence": 72 if item.get("risk_label") else 65,
                "status": item.get("status") or "DRAFT_REVIEW",
                "task_type": "NEMESIS_CROSSCHECK_REQUIRED",
                "budget": budget,
                "waste_potential": waste,
                "agency": item.get("agency", ""),
                "satker": item.get("satker", ""),
            }
        )
    return out


def ai_data_builder_rows(items: list[dict]) -> dict[int, list[dict[str, str]]]:
    grouped: dict[int, list[dict[str, str]]] = {}
    for item in items:
        year = int(item["year"])
        cid = "HUNTER-" + stable_id(item["id"], "builder")
        grouped.setdefault(year, []).append(
            {
                "tahun": str(year),
                "col": cid,
                "Module": item["module"],
                "Record": item["title"],
                "Jenis_Saran": item["source_type"],
                "Field": "source_candidate",
                "Usulan": compact_text(item["summary"], item["link"]),
                "Risk": risk_level(int(item["confidence"])),
                "Status": "DRAFT_REVIEW_NEEDS_EVIDENCE" if int(item["confidence"]) >= 50 else "SOURCE_PATROL_REQUIRED",
                "Alias": item["id"],
                "Canonical": item["link"],
                "Tipe": item["task_type"],
                "Confidence": str(item["confidence"]),
                "Aksi": "AI_AUDIT_AND_MAP_TO_FINAL_MODULE",
            }
        )
    return grouped


def ai_pengawas_rows(items: list[dict]) -> dict[int, list[dict[str, str]]]:
    grouped: dict[int, list[dict[str, str]]] = {}
    for item in items:
        year = int(item["year"])
        cid = "WATCH-" + stable_id(item["id"], "pengawas")
        grouped.setdefault(year, []).append(
            {
                "tahun": str(year),
                "Bln_Thn": f"{item.get('month') or '0'}/{year}",
                "Akun": "AI_HUNTER_DRAFT",
                "Keterangan": item["title"],
                "Kredit_Rp": money_label(parse_money(item["summary"])),
                "Status": "DRAFT_REVIEW_NEEDS_EVIDENCE",
                "Tgl": now_jakarta()[:10],
                "No_Bukti": item["link"],
                "Debet": "",
                "Kredit": "",
                "Saldo": "",
                "Aksi": "AUDIT_VALIDATE_PROMOTE",
                "Modul": item["module"],
                "ID": item["id"],
                "Data": compact_text(item["summary"], item["source"]),
                "Dihapus_Pada": "",
            }
        )
    return grouped


def module_row(item: dict) -> dict[str, str] | None:
    module = str(item["module"])
    year = str(item["year"])
    cid = "AIH-" + stable_id(item["id"], module)
    title = item["title"]
    summary = item["summary"]
    link = item["link"]
    confidence = int(item["confidence"])
    loss = money_label(parse_money(summary))
    if module == "korupsi":
        return {
            "tahun": year,
            "col": cid,
            "Nama_Kasus": title,
            "Tahun": year,
            "Status_Hukum": "DRAFT_REVIEW_NEEDS_OFFICIAL_EVIDENCE",
            "Kasus": title,
            "Nilai_Kerugian": loss,
            "Kerugian": loss,
            "Sumber_Perhitungan": item["source"],
            "Status_Verifikasi": "AI_HUNTER_DRAFT_REVIEW",
            "Sumber_Temuan": item["source_type"],
            "Ringkasan_Temuan": compact_text(summary),
            "Status_Tindak_Lanjut": "AI_AUDIT_REQUIRED",
            "Link_Referensi": link,
            "Risk_Score": str(confidence),
        }
    if module in {"redflag", "risknas"}:
        return {
            "tahun": year,
            "col": cid,
            "Tipe": item["source_type"],
            "Instansi_Program": item.get("agency") or item["source"],
            "Deskripsi": compact_text(title, summary),
            "Bukti": link,
            "Level": risk_level(confidence),
            "Status": "DRAFT_REVIEW_NEEDS_CROSSCHECK",
            "Dilaporkan": now_jakarta()[:10],
        }
    if module == "vendor":
        return {
            "tahun": year,
            "col": cid,
            "Nama_Vendor": "AI_HUNTER_NEEDS_VENDOR_EXTRACTION",
            "Total_Kontrak": loss,
            "Instansi": item["source"],
            "Nilai_Total": loss,
            "Risk_Score": str(confidence),
            "Status": compact_text(title, link, limit=180),
        }
    if module == "audit":
        return {
            "tahun": year,
            "col": cid,
            "Program": title,
            "Dasar_Hukum": link,
            "Status_Audit": "DRAFT_REVIEW_NEEDS_EVIDENCE",
            "Total_Anggaran": loss,
            "Realisasi": "",
            "PIC": item["source"],
            "Sasaran": compact_text(summary, limit=160),
        }
    if module in {"prog_daerah", "prog_eksekutif", "prog_legislatif"}:
        return {
            "tahun": year,
            "col": cid,
            "Program": title,
            "Dasar_Hukum": link,
            "Anggaran": loss,
            "Output": compact_text(summary, limit=160),
            "Status": "DRAFT_REVIEW_NEEDS_EVIDENCE",
            "Sumber_Dana": "APBN/APBD_NEEDS_MAPPING",
            "Keterangan": item["source_type"],
        }
    if module == "bea_cukai":
        return {
            "tahun": year,
            "col": cid,
            "Tahun": year,
            "Bulan": item.get("month") or "0",
            "Jenis": title,
            "Penerimaan": loss,
            "Dokumen": link,
            "Status": "DRAFT_REVIEW_NEEDS_EVIDENCE",
            "Severity": risk_level(confidence),
            "Indikasi": compact_text(summary, limit=160),
            "Evidence": item["source"],
        }
    if module == "pajak":
        return {
            "tahun": year,
            "col": cid,
            "Jenis_Pajak": "AI_HUNTER_SIGNAL",
            "Objek_Sasaran": title,
            "Tahun": year,
            "Bulan": item.get("month") or "0",
            "Nilai": loss,
        }
    if module == "sda":
        return {
            "tahun": year,
            "col": cid,
            "Sektor": "AI_HUNTER_SIGNAL",
            "Komoditas_Sumber": item["source"],
            "Keterangan": compact_text(title, summary, link),
            "Tahun": year,
            "Bulan": item.get("month") or "0",
            "Nilai_Ekonomi": loss,
        }
    if module == "bumn":
        return {
            "tahun": year,
            "col": cid,
            "Level": "AI_HUNTER_SIGNAL",
            "Jabatan": title,
            "Fasilitas": compact_text(summary, link, limit=180),
        }
    return None


def module_rows(items: list[dict]) -> dict[tuple[str, int], list[dict[str, str]]]:
    grouped: dict[tuple[str, int], list[dict[str, str]]] = {}
    for item in items:
        module = str(item["module"])
        if item.get("source_type") == "PUBLIC_SUBMISSION" and int(item.get("confidence") or 0) < 50:
            continue
        if module not in MODULE_TARGETS:
            continue
        row = module_row(item)
        if not row:
            continue
        grouped.setdefault((module, int(item["year"])), []).append(row)
    return grouped


def prune_unsafe_public_module_rows(items: list[dict]) -> int:
    removed = 0
    for item in items:
        if item.get("source_type") != "PUBLIC_SUBMISSION" or int(item.get("confidence") or 0) >= 50:
            continue
        module = str(item.get("module") or "")
        if module not in MODULE_TARGETS:
            continue
        path = MODERN_DIR / f"{module}_{int(item['year'])}.csv"
        fields, rows = read_rows(path)
        if not fields:
            continue
        stale_key = "AIH-" + stable_id(item["id"], module)
        kept = [row for row in rows if row.get("col", "") != stale_key]
        if len(kept) == len(rows):
            continue
        write_rows(path, fields, kept)
        removed += len(rows) - len(kept)
    return removed


def count_rows_with_prefix(pattern: str, field: str, prefix: str) -> int:
    total = 0
    for path in MODERN_DIR.glob(pattern):
        _, rows = read_rows(path)
        total += sum(1 for row in rows if row.get(field, "").startswith(prefix))
    return total


def main() -> int:
    fallback_year = active_year()
    generated_at = now_jakarta()
    items = normalize_ai_candidates(fallback_year)
    items.extend(normalize_public_submissions(fallback_year))
    items.extend(normalize_nemesis_candidates(fallback_year))

    added_builder = 0
    added_watch = 0
    added_modules: dict[str, int] = {}
    pruned_public_rows = prune_unsafe_public_module_rows(items)

    for year, rows in ai_data_builder_rows(items).items():
        path = MODERN_DIR / f"ai_data_builder_{year}.csv"
        added_builder += upsert_rows(path, rows)
    for year, rows in ai_pengawas_rows(items).items():
        path = MODERN_DIR / f"ai_pengawas_{year}.csv"
        added_watch += upsert_rows(path, rows, "ID")
    for (module, year), rows in module_rows(items).items():
        path = MODERN_DIR / f"{module}_{year}.csv"
        added = upsert_rows(path, rows)
        added_modules[f"{module}_{year}"] = added_modules.get(f"{module}_{year}", 0) + added

    status = {
        "generated_at": generated_at,
        "engine": "MR_AI_HUNTER_PROMOTION",
        "purpose": "Promosi otomatis kandidat Data Hunter ke Gudang DB draft agar tidak berhenti di queue.",
        "input_candidates_seen": len(items),
        "added_ai_data_builder_rows": added_builder,
        "added_ai_pengawas_rows": added_watch,
        "added_module_draft_rows": sum(added_modules.values()),
        "pruned_unsafe_public_module_rows": pruned_public_rows,
        "total_ai_data_builder_hunter_rows": count_rows_with_prefix("ai_data_builder_*.csv", "col", "HUNTER-"),
        "total_ai_pengawas_hunter_rows": count_rows_with_prefix("ai_pengawas_*.csv", "ID", "MR-"),
        "total_module_ai_hunter_draft_rows": count_rows_with_prefix("*.csv", "col", "AIH-"),
        "added_by_module_year": dict(sorted(added_modules.items())),
        "hardcoded_rules": [
            "Tidak ada kandidat hunter yang hanya ditelan; minimal masuk ai_data_builder/ai_pengawas draft.",
            "Data belum final wajib berstatus DRAFT_REVIEW/NEEDS_EVIDENCE.",
            "Baris modul final hanya draft dan wajib cross-check sumber resmi atau dua sumber independen.",
        ],
    }
    STATUS_JSON.write_text(json.dumps(status, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"AI Hunter inputs: {len(items)}")
    print(f"Added ai_data_builder rows: {added_builder}")
    print(f"Added ai_pengawas rows: {added_watch}")
    print(f"Added module draft rows: {sum(added_modules.values())}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
