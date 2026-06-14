from __future__ import annotations

import argparse
import csv
import json
import re
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo


ROOT = Path(__file__).resolve().parents[1]
GUDANG_DB = ROOT / "gudang-db"
AI_INDEX = GUDANG_DB / "_index" / "ai_index.json"
ACTIVE_PERIOD = ROOT / "dashboard" / "active-period.json"
SUMMARY = ROOT / "dashboard" / "dashboard_summary.json"
JSON_OUT = ROOT / "dashboard" / "pre_github_readiness.json"
TASKS_OUT = ROOT / "dashboard" / "ai_agent_tasks.json"
MD_OUT = ROOT / "docs" / "PRE_GITHUB_READINESS_REPORT.md"

CORE_MODULES = {
    "akuntansi",
    "audit",
    "audittrail",
    "bea_cukai",
    "bumn",
    "korupsi",
    "pajak",
    "parpol",
    "prog_daerah",
    "prog_eksekutif",
    "prog_legislatif",
    "redflag",
    "risknas",
    "sda",
    "vendor",
}

SOURCE_COLUMNS = {
    "sumber",
    "source",
    "dokumen",
    "evidence",
    "link",
    "link_referensi",
    "link_ref_kpk",
    "link_ref_ma",
    "link_ref_bpk",
    "putusan_sumber",
    "sumber_bpk",
    "sumber_kpk",
    "sumber_perhitungan",
}

MONEY_COLUMNS = {
    "kerugian",
    "nilai_kerugian",
    "kerugian_diakibatkan",
    "total_kerugian",
    "potensi_kerugian",
    "nilai",
    "nilai_ekonomi",
    "nilai_barang",
    "penerimaan",
    "debet_rp",
    "kredit_rp",
    "saldo_rp",
    "pagu_apbn",
    "realisasi",
}

MASTER_FALLBACKS = {
    "korupsi": "master_koruptor.csv",
    "vendor": "master_vendor.csv",
    "bumn": "master_koruptor.csv",
    "risknas": "master_koruptor.csv",
}

SOURCE_PRIORITIES = {
    "akuntansi": ["Kemenkeu APBN KiTa", "LKPP/SiRUP", "BPK"],
    "audit": ["BPK", "KPK", "Kejaksaan", "LKPP", "Kompas/Detik/Tempo sebagai pembanding"],
    "audittrail": ["BPK", "LKPP", "K/L pemilik program"],
    "bea_cukai": ["Kemenkeu/DJBC", "BPK", "KPK", "Kejaksaan", "putusan pengadilan", "Kompas/Detik/Tempo/Metro TV"],
    "bumn": ["Laporan keuangan BUMN", "BPK", "KPK", "Kejaksaan", "CNBC/Kompas/Detik/Tempo"],
    "korupsi": ["KPK", "Kejaksaan", "BPK", "Putusan MA", "Kompas/Detik/Tempo/Metro TV/CNN", "Nemesis sebagai acuan awal non-final"],
    "pajak": ["Kemenkeu/DJP", "BPK", "putusan pengadilan", "Kompas/Detik/CNBC"],
    "parpol": ["KPU", "BPK", "Kemendagri", "APBN/APBD", "Kompas/Detik/Tempo"],
    "prog_daerah": ["LKPP/SiRUP", "APBD", "BPK", "Kompas/Detik/Tempo", "Nemesis"],
    "prog_eksekutif": ["LKPP/SiRUP", "Kemenkeu", "BPK", "Kompas/Detik/Tempo", "Nemesis"],
    "prog_legislatif": ["LKPP/SiRUP", "DPR/DPRD", "BPK", "Kompas/Detik/Tempo", "Nemesis"],
    "redflag": ["LKPP/SiRUP", "BPK", "KPK", "Kompas/Detik/Tempo/Metro TV", "Nemesis"],
    "risknas": ["BPK", "KPK", "Kejaksaan", "LKPP/SiRUP", "Kompas/Detik/Tempo/CNN", "Nemesis"],
    "sda": ["ESDM", "KLHK", "KKP", "BPK", "KPK"],
    "vendor": ["LKPP/SiRUP", "LPSE", "Kompas/Detik/Tempo", "Nemesis", "AHU/beneficial ownership"],
}


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        rows = []
        for row in reader:
            clean = {str(k or "").strip(): str(v or "").strip() for k, v in row.items()}
            if any(clean.values()):
                rows.append(clean)
        return rows


def parse_year(value: str, fallback: int = 0) -> int:
    match = re.search(r"(19\d{2}|20\d{2})", str(value or ""))
    return int(match.group(1)) if match else fallback


def parse_month(value: str) -> int:
    text = str(value or "").strip().lower()
    if not text:
        return 0
    month_names = {
        "januari": 1,
        "februari": 2,
        "maret": 3,
        "april": 4,
        "mei": 5,
        "juni": 6,
        "juli": 7,
        "agustus": 8,
        "september": 9,
        "oktober": 10,
        "november": 11,
        "desember": 12,
    }
    if text in month_names:
        return month_names[text]
    match = re.search(r"\b(1[0-2]|0?[1-9])\b", text)
    return int(match.group(1)) if match else 0


def normalized(row: dict[str, str]) -> dict[str, str]:
    return {str(k).strip().lower(): v for k, v in row.items()}


def has_source(row: dict[str, str]) -> bool:
    lower = normalized(row)
    return any(lower.get(col) for col in SOURCE_COLUMNS)


def has_money(row: dict[str, str]) -> bool:
    lower = normalized(row)
    return any(lower.get(col) for col in MONEY_COLUMNS)


def module_year_from_path(path: Path) -> tuple[str, int]:
    match = re.match(r"(.+)_((?:19|20)\d{2})\.csv$", path.name, re.IGNORECASE)
    if not match:
        return path.stem, 0
    return match.group(1), int(match.group(2))


def latest_year_from_rows(rows: list[dict[str, str]], fallback: int = 0) -> int:
    years = [parse_year(value, 0) for row in rows for value in row.values()]
    years = [year for year in years if year]
    return max(years) if years else fallback


def inspect_master_fallback(module: str) -> dict:
    file_name = MASTER_FALLBACKS.get(module)
    if not file_name:
        return {"status": "NO_FALLBACK", "file": "", "rows": 0, "year": 0}
    path = GUDANG_DB / "master" / file_name
    if not path.exists():
        return {"status": "MISSING_MASTER", "file": file_name, "rows": 0, "year": 0}
    rows = read_rows(path)
    if not rows:
        return {"status": "MASTER_EMPTY", "file": f"gudang-db/master/{file_name}", "rows": 0, "year": 0}
    return {
        "status": "MASTER_HISTORY_AVAILABLE",
        "file": f"gudang-db/master/{file_name}",
        "rows": len(rows),
        "year": latest_year_from_rows(rows),
    }


def active_row(row: dict[str, str], file_year: int, active_year: int, active_month: int) -> bool:
    lower = normalized(row)
    year = parse_year(lower.get("tahun") or lower.get("year") or lower.get("tahun_data"), file_year)
    if year != active_year:
        return False
    month_value = lower.get("bulan") or lower.get("bln") or lower.get("bulan_data") or lower.get("bln_thn")
    month = parse_month(month_value)
    return month in (0, active_month)


def build_payload() -> dict:
    index = read_json(AI_INDEX)
    active = read_json(ACTIVE_PERIOD)
    summary = read_json(SUMMARY) if SUMMARY.exists() else {}
    now = datetime.now(ZoneInfo("Asia/Jakarta"))
    active_year = int(active["year"])
    active_month = int(active["month"])
    expected_years = set(range(1966, active_year + 1))

    modules: dict[str, dict] = {}
    for module, meta in sorted(index.get("modules", {}).items()):
        years = {int(y) for y in meta.get("years", {}).keys()}
        missing = sorted(expected_years - years)
        modules[module] = {
            "years_present": len(years & expected_years),
            "years_expected": len(expected_years),
            "missing_years": missing,
            "structural_status": "OK" if not missing else "MISSING_YEARS",
            "rows_total": 0,
            "rows_with_source": 0,
            "rows_with_money": 0,
            "active_rows": 0,
            "active_rill_rows": 0,
            "latest_nonempty_year": 0,
            "latest_nonempty_rows": 0,
            "fallback": inspect_master_fallback(module),
            "data_status": "NEEDS_DATA",
        }

    for path in sorted(GUDANG_DB.rglob("*.csv")):
        if path.parent.name == "master" or path.parent.name == "_index":
            continue
        module, file_year = module_year_from_path(path)
        if module not in modules:
            continue
        rows = read_rows(path)
        info = modules[module]
        info["rows_total"] += len(rows)
        if rows and file_year >= info["latest_nonempty_year"]:
            info["latest_nonempty_year"] = file_year
            info["latest_nonempty_rows"] = len(rows)
        for row in rows:
            source = has_source(row)
            money = has_money(row)
            if source:
                info["rows_with_source"] += 1
            if money:
                info["rows_with_money"] += 1
            if active_row(row, file_year, active_year, active_month):
                info["active_rows"] += 1
                if source and money:
                    info["active_rill_rows"] += 1

    for info in modules.values():
        if info["rows_total"] and info["rows_with_source"]:
            info["data_status"] = "HAS_EVIDENCE"
        elif info["rows_total"]:
            info["data_status"] = "HAS_ROWS_NO_EVIDENCE"

    core = {k: modules.get(k) for k in sorted(CORE_MODULES) if k in modules}
    missing_core = sorted(CORE_MODULES - set(modules))
    active_mismatch = now.year != active_year or now.month != active_month
    active_total = sum(item["active_rows"] for item in modules.values())
    active_rill_total = sum(item["active_rill_rows"] for item in modules.values())
    structural_missing = [k for k, v in modules.items() if v["structural_status"] != "OK"]
    core_needs_data = [k for k, v in core.items() if v and v["data_status"] == "NEEDS_DATA"]
    tasks = []
    for module, info in core.items():
        if not info:
            continue
        if info["active_rill_rows"] > 0:
            continue
        fallback = info["fallback"]
        fallback_note = (
            f"Pakai fallback {fallback['file']} tahun terakhir {fallback['year']}"
            if fallback.get("status") == "MASTER_HISTORY_AVAILABLE"
            else "Belum ada fallback lokal berisi data; tampilkan notifikasi data belum bersumber"
        )
        tasks.append(
            {
                "module": module,
                "year": active_year,
                "month": active_month,
                "status": "SEARCH_REQUIRED",
                "priority": "HIGH" if module in {"akuntansi", "korupsi", "bea_cukai", "sda", "vendor", "redflag"} else "MEDIUM",
                "fallback": fallback,
                "fallback_note": fallback_note,
                "source_priorities": SOURCE_PRIORITIES.get(module, ["Sumber resmi pemerintah", "BPK", "LKPP/SiRUP"]),
                "instruction": "Tim AI Agent harus mencari sumber publik/resmi, membuat draft CSV, memberi status DRAFT_REVIEW, dan tidak mengklaim final sebelum evidence diverifikasi.",
            }
        )

    status = "READY_WITH_EMPTY_CURRENT_PERIOD"
    blockers = []
    if active_mismatch:
        blockers.append("dashboard/active-period.json tidak sama dengan tanggal Asia/Jakarta saat ini")
    if missing_core:
        blockers.append("ada modul inti yang belum ada di Gudang DB")
    if structural_missing:
        blockers.append("ada modul yang belum lengkap file tahunnya")
    if active_rill_total == 0:
        blockers.append("belum ada baris data riil bersumber untuk tahun/bulan berjalan")
    if blockers:
        status = "NEEDS_WORK"

    return {
        "generated_at": now.isoformat(timespec="seconds"),
        "active_period": active,
        "current_jakarta": {"year": now.year, "month": now.month},
        "status": status,
        "blockers": blockers,
        "modules_count": len(modules),
        "core_modules_count": len(core),
        "missing_core_modules": missing_core,
        "structural_missing_modules": structural_missing,
        "current_period_rows": active_total,
        "current_period_rill_rows": active_rill_total,
        "ai_agent_tasks_count": len(tasks),
        "ai_agent_tasks_file": "dashboard/ai_agent_tasks.json",
        "dashboard_summary": summary,
        "core_modules": core,
        "modules": modules,
        "ai_agent_tasks": tasks,
    }


def write_report(payload: dict) -> None:
    lines = [
        "# Pre-GitHub Readiness Report",
        "",
        f"Generated: {payload['generated_at']} Asia/Jakarta",
        f"Status: **{payload['status']}**",
        "",
        "## Active Period Gate",
        "",
        f"- Dashboard active period: {payload['active_period']['month_name']} {payload['active_period']['year']}",
        f"- Current Asia/Jakarta: {payload['current_jakarta']['month']} / {payload['current_jakarta']['year']}",
        f"- Current period rows: {payload['current_period_rows']}",
        f"- Current period rill rows with source + nominal: {payload['current_period_rill_rows']}",
        f"- AI Agent search tasks: {payload['ai_agent_tasks_count']}",
        "",
        "## Blockers",
        "",
    ]
    if payload["blockers"]:
        lines.extend(f"- {item}" for item in payload["blockers"])
    else:
        lines.append("- Tidak ada blocker struktural.")
    lines.extend([
        "",
        "## Core Sector Coverage",
        "",
        "| Modul | Tahun | Rows | Source | Nominal | Active Rows | Active Rill | Status |",
        "|---|---:|---:|---:|---:|---:|---:|---|",
    ])
    for module, info in payload["core_modules"].items():
        lines.append(
            f"| {module} | {info['years_present']}/{info['years_expected']} | {info['rows_total']} | "
            f"{info['rows_with_source']} | {info['rows_with_money']} | {info['active_rows']} | "
            f"{info['active_rill_rows']} | {info['structural_status']} / {info['data_status']} |"
        )
    lines.extend([
        "",
        "## Fallback & AI Agent",
        "",
        "- Jika periode berjalan kosong, dashboard boleh menampilkan fallback historis/master dengan label jelas.",
        "- Fallback tidak boleh dianggap data riil tahun/bulan berjalan.",
        "- Daftar tugas pencarian otomatis ditulis ke `dashboard/ai_agent_tasks.json`.",
        "- Website seperti Nemesis dapat dipakai sebagai acuan awal untuk pengadaan/redflag, tetapi harus diberi status review dan diverifikasi ke LKPP/SiRUP/BPK/KPK/Kejaksaan/putusan.",
        "",
        "## Catatan",
        "",
        "- `OK / NEEDS_DATA` berarti file sektor dan tahun tersedia, tetapi isinya masih header/template.",
        "- `active_rill_rows` hanya menghitung baris tahun/bulan berjalan yang punya sumber/evidence dan nominal.",
        "- Jika current period kosong, HTML wajib menampilkan nol/ringkasan kosong dan mengarahkan detail ke Gudang DB.",
        "- Tim AI Agent harus mengisi queue draft dengan sumber resmi sebelum data naik menjadi data publik.",
        "",
    ])
    MD_OUT.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true", help="Write JSON and Markdown reports.")
    parser.add_argument("--strict", action="store_true", help="Return non-zero when blockers exist.")
    args = parser.parse_args()

    payload = build_payload()
    if args.write:
        JSON_OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        TASKS_OUT.write_text(json.dumps(payload["ai_agent_tasks"], ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        write_report(payload)
        print(f"Wrote {JSON_OUT.relative_to(ROOT)}")
        print(f"Wrote {TASKS_OUT.relative_to(ROOT)}")
        print(f"Wrote {MD_OUT.relative_to(ROOT)}")
    print(f"Pre-GitHub readiness: {payload['status']}")
    print(f"Modules: {payload['modules_count']} | Core: {payload['core_modules_count']}")
    print(f"Current period rill rows: {payload['current_period_rill_rows']}")
    print(f"AI Agent tasks: {payload['ai_agent_tasks_count']}")
    for blocker in payload["blockers"][:20]:
        print(f"BLOCKER: {blocker}")
    return 1 if args.strict and payload["blockers"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
