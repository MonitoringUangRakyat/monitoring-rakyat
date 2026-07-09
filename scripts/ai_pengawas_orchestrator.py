from __future__ import annotations

import csv
import hashlib
import html
import json
import re
import sys
import time
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from datetime import datetime
from email.utils import parsedate_to_datetime
from pathlib import Path
from zoneinfo import ZoneInfo


ROOT = Path(__file__).resolve().parents[1]
GUDANG_DB = ROOT / "gudang-db"
QUEUE_DIR = GUDANG_DB / "_queue"
FEEDS = GUDANG_DB / "master" / "master_source_feeds.csv"
TASKS = ROOT / "dashboard" / "ai_agent_tasks.json"
SOURCE_PATROL = ROOT / "dashboard" / "ai_agent_source_patrol.json"
CANDIDATES_JSON = QUEUE_DIR / "ai_pengawas_candidates.json"
CANDIDATES_CSV = QUEUE_DIR / "ai_pengawas_candidates.csv"
PUBLIC_SUBMISSIONS_JSON = QUEUE_DIR / "public_submissions.json"
STATUS_JSON = ROOT / "dashboard" / "ai_orchestrator_status.json"
REPORT_MD = ROOT / "docs" / "AI_ORCHESTRATOR_24_7_REPORT.md"

USER_AGENT = "MonitoringRakyat-AIPengawas/1.0 (+https://github.com/MonitoringUangRakyat/monitoring-rakyat)"
MAX_FEEDS_PER_RUN = 10_000
MAX_ITEMS_PER_FEED = 75
MAX_TOTAL_NEW = 2_500
AUTONOMOUS_TOOL_MANDATE = {
    "hardcoded": True,
    "mode": "FULL_MANDIRI_PROAKTIF_24_7",
    "principle": "Semua tool/sumber yang tersedia wajib dimanfaatkan untuk memperlengkap Gudang DB tanpa menunggu instruksi manual.",
    "no_artificial_limit": True,
    "only_allowed_limits": [
        "batas waktu/kuota platform GitHub Actions atau backend worker",
        "safety guard: tidak mempublish klaim final tanpa evidence",
        "dedupe agar data tidak berulang",
        "rate-limit sopan ke sumber publik/resmi",
    ],
    "must_use_available_tools": [
        "RSS/feed publik yang aktif",
        "GitHub public submissions",
        "Nemesis intake jika data tersedia",
        "Gudang DB index/validator",
        "source patrol",
        "AI hunter promotion",
        "dashboard/fiscal/dashboard summary sync",
    ],
    "minimum_runtime": "GitHub Actions dijadwalkan setiap jam; backend worker eksternal boleh menjalankan loop lebih rapat bila tersedia.",
}
DAILY_FLOW_CONTROLLER = {
    "id": "AI_KOORDINATOR_ALUR_HARIAN",
    "name": "AI Koordinator Alur Harian",
    "hardcoded": True,
    "mission": "Mengatur urutan kerja harian agar Gudang DB, dashboard, patrol, dan draft queue selalu sinkron tanpa perlu diingatkan manual.",
    "daily_hardcoded_tasks": [
        "generate_ai_index.py",
        "validate_gudang_db.py",
        "validate_immutable_db.py",
        "build_dashboard_summary.py",
        "build_fiscal_ratio_summary.py",
        "import_nemesis_procurement.py",
        "import_public_submissions.py",
        "pre_github_readiness.py --write",
        "build_source_patrol.py",
        "ai_pengawas_orchestrator.py",
        "promote_ai_hunter_candidates.py",
    ],
    "must_keep_in_sync": [
        "gudang-db/_index/ai_index.json",
        "dashboard/dashboard_summary.json",
        "dashboard/fiscal_ratio_annual.json",
        "dashboard/nemesis_integration_status.json",
        "dashboard/pre_github_readiness.json",
        "dashboard/ai_agent_tasks.json",
        "dashboard/ai_agent_source_patrol.json",
        "dashboard/ai_orchestrator_status.json",
        "dashboard/ai_hunter_promotion_status.json",
        "gudang-db/_queue/ai_pengawas_candidates.json",
        "gudang-db/_queue/nemesis_procurement_candidates.json",
        "gudang-db/_queue/public_submissions.json",
    ],
    "cashflow_rule": "Setiap Rp 1 APBN/APBD harus diarahkan ke modul, periode, nominal, sumber, evidence, dan status verifikasi.",
    "autonomous_tool_mandate": AUTONOMOUS_TOOL_MANDATE,
}
PUBLIC_DB_UPLOAD_POLICY = {
    "hardcoded": True,
    "entry_status": "DRAFT_PUBLIC_SUBMISSION",
    "accepted_inputs": [
        "link_sumber",
        "excel",
        "word",
        "pdf",
        "catatan_noted",
        "csv",
        "teks_biasa",
    ],
    "triage_thresholds": {
        "minimum_queue_score": 50,
        "search_task_score_min": 40,
        "reject_below_score": 40,
    },
    "routing": {
        "score_50_or_more": "Masuk audit queue Gudang DB sesegera mungkin untuk analisa, dedupe, evidence check, nominal/periode, dan mapping halaman/menu.",
        "score_40_to_49": "Simpan sebagai task pencarian pembanding; belum boleh menjadi klaim publik.",
        "score_below_40": "Audit ketat link/dokumen/sumber; fake/spam/fitnah/doxing/tidak bisa dicek wajib REJECTED_FAKE_OR_UNVERIFIABLE.",
    },
    "page_update_rule": "Data yang lolos audit minimal wajib memicu sinkronisasi Gudang DB dan tampil di halaman/menu terkait secepat workflow validasi memungkinkan.",
}

OFFICIAL_CATEGORIES = {
    "OFFICIAL_AUDIT",
    "OFFICIAL_BUDGET",
    "OFFICIAL_COURT",
    "OFFICIAL_CUSTOMS",
    "OFFICIAL_ENFORCEMENT",
    "OFFICIAL_PROCUREMENT",
}
SENSITIVE_MODULES = {"korupsi", "bumn", "bea_cukai", "pajak", "sda", "vendor", "redflag", "risknas"}
MONEY_HINTS = re.compile(
    r"\b(apbn|apbd|anggaran|belanja|pagu|realisasi|kontrak|tender|pajak|cukai|bea|hibah|subsidi|bansos|kerugian|rp|triliun|miliar|juta)\b",
    re.IGNORECASE,
)
KEYWORDS_BY_MODULE = {
    "akuntansi": ["apbn", "realisasi anggaran", "belanja negara", "kemenkeu", "dipa", "spm", "sp2d"],
    "audit": ["temuan bpk", "audit", "kerugian negara", "bpk", "laporan hasil pemeriksaan"],
    "audittrail": ["audit pengadaan", "temuan audit", "tindak lanjut bpk", "dokumen pengadaan"],
    "bea_cukai": ["bea cukai", "djbc", "cukai ilegal", "penyelundupan", "kepabeanan"],
    "bumn": ["bumn", "kerugian negara", "korupsi bumn", "laporan keuangan"],
    "korupsi": ["korupsi", "kerugian negara", "tersangka", "putusan", "kpk", "kejaksaan"],
    "pajak": ["pajak", "djp", "penggelapan pajak", "penerimaan pajak", "tax ratio"],
    "parpol": ["dana parpol", "bantuan partai politik", "hibah organisasi", "kpu"],
    "prog_daerah": ["apbd", "proyek daerah", "pengadaan daerah", "dprd", "pemda"],
    "prog_eksekutif": ["proyek kementerian", "pengadaan kementerian", "apbn", "program pemerintah"],
    "prog_legislatif": ["dpr", "dprd", "anggaran legislatif", "reses", "rumah jabatan"],
    "redflag": ["tender bermasalah", "proyek bermasalah", "red flag", "pengadaan", "vendor"],
    "risknas": ["risiko korupsi", "kerugian negara", "pengadaan bermasalah", "indeks risiko"],
    "sda": ["tambang ilegal", "kehutanan", "perikanan", "sda", "royalti", "pnbp"],
    "vendor": ["vendor", "pemenang tender", "lpse", "sirup", "kontrak", "beneficial owner"],
}


@dataclass
class Feed:
    id: str
    name: str
    category: str
    domain: str
    feed_url: str
    confidence: int


def now_jakarta() -> datetime:
    return datetime.now(ZoneInfo("Asia/Jakarta"))


def read_json(path: Path, fallback):
    if not path.exists():
        return fallback
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except Exception:
        return fallback


def write_json(path: Path, payload) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return [{str(k or "").strip(): str(v or "").strip() for k, v in row.items()} for row in csv.DictReader(handle)]


def load_feeds() -> list[Feed]:
    feeds = []
    for row in read_csv_rows(FEEDS):
        if not row.get("feed_url"):
            continue
        if row.get("status", "").upper() not in {"ACTIVE", "CANDIDATE"}:
            continue
        try:
            confidence = int(row.get("confidence_awal") or 0)
        except ValueError:
            confidence = 0
        feeds.append(
            Feed(
                id=row.get("id", ""),
                name=row.get("nama_sumber", ""),
                category=row.get("kategori", ""),
                domain=row.get("domain", ""),
                feed_url=row.get("feed_url", ""),
                confidence=confidence,
            )
        )
    return feeds


def fetch_url(url: str, timeout: int = 20) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/rss+xml, application/xml, text/xml, */*"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read()


def strip_text(value: str | None) -> str:
    text = html.unescape(str(value or ""))
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def xml_text(node: ET.Element, names: tuple[str, ...]) -> str:
    for name in names:
        found = node.find(name)
        if found is not None and found.text:
            return strip_text(found.text)
    for child in node:
        local = child.tag.split("}")[-1].lower()
        if local in {item.lower().split(":")[-1] for item in names} and child.text:
            return strip_text(child.text)
    return ""


def xml_link(node: ET.Element) -> str:
    link = xml_text(node, ("link", "guid"))
    if link:
        return link
    for child in node:
        local = child.tag.split("}")[-1].lower()
        if local == "link":
            href = child.attrib.get("href")
            if href:
                return href.strip()
    return ""


def parse_feed(raw: bytes) -> list[dict[str, str]]:
    root = ET.fromstring(raw)
    nodes = root.findall(".//item") or root.findall(".//{http://www.w3.org/2005/Atom}entry")
    items = []
    for node in nodes[:MAX_ITEMS_PER_FEED]:
        title = xml_text(node, ("title",))
        link = xml_link(node)
        published = xml_text(node, ("pubDate", "published", "updated", "dc:date"))
        summary = xml_text(node, ("description", "summary", "content"))
        if not title and not link:
            continue
        items.append({"title": title, "link": link, "published": normalize_date(published), "summary": summary})
    return items


def normalize_date(value: str) -> str:
    value = strip_text(value)
    if not value:
        return ""
    try:
        return parsedate_to_datetime(value).isoformat()
    except Exception:
        return value[:80]


def task_keywords(task: dict) -> list[str]:
    module = str(task.get("module") or "")
    values: list[str] = list(KEYWORDS_BY_MODULE.get(module, []))
    values.extend([module, module.replace("_", " ")])
    year = str(task.get("year") or "")
    if year:
        values.append(year)
    seen = set()
    out = []
    for value in values:
        clean = str(value).strip().lower()
        if clean and clean not in seen:
            seen.add(clean)
            out.append(clean)
    return out[:16]


def score_item(task: dict, feed: Feed, item: dict[str, str]) -> tuple[int, list[str]]:
    text = " ".join([item.get("title", ""), item.get("summary", "")]).lower()
    reasons = []
    relevance = 0
    for keyword in task_keywords(task):
        if keyword and keyword in text:
            relevance += 15
            reasons.append(f"keyword:{keyword}")
    if str(task.get("year") or "") in text:
        relevance += 4
        reasons.append("year_match")
    if MONEY_HINTS.search(text):
        relevance += 10
        reasons.append("cashflow_hint")
    if feed.category in OFFICIAL_CATEGORIES:
        relevance += 12
        reasons.append("official_source")
    if feed.category == "MAINSTREAM_MEDIA":
        reasons.append("media_signal")
    if not any(reason.startswith("keyword:") for reason in reasons):
        return 0, []
    if module_is_sensitive(str(task.get("module") or "")) and "cashflow_hint" not in reasons and feed.category not in OFFICIAL_CATEGORIES:
        return 0, []
    confidence = int(feed.confidence * 0.55) + relevance
    return max(0, min(100, confidence)), reasons[:8]


def module_is_sensitive(module: str) -> bool:
    return module in SENSITIVE_MODULES


def candidate_id(module: str, link: str, title: str) -> str:
    raw = f"{module}|{link}|{title}".encode("utf-8", "ignore")
    return "MR-AI-" + hashlib.sha256(raw).hexdigest()[:16].upper()


def policy_status(module: str, feed: Feed, score: int) -> str:
    if feed.category in OFFICIAL_CATEGORIES and score >= 85:
        return "VERIFIED_SOURCE_CANDIDATE"
    if module in SENSITIVE_MODULES:
        return "DRAFT_REVIEW"
    if score >= 75:
        return "DRAFT_REVIEW"
    return "AI_CLASSIFIED_NEEDS_VERIFICATION"


def existing_candidate_ids() -> set[str]:
    payload = read_json(CANDIDATES_JSON, {"candidates": []})
    return {str(item.get("id")) for item in payload.get("candidates", [])}


def make_candidate(task: dict, feed: Feed, item: dict[str, str], score: int, reasons: list[str], generated_at: str) -> dict:
    module = str(task.get("module") or "unknown")
    cid = candidate_id(module, item.get("link", ""), item.get("title", ""))
    status = policy_status(module, feed, score)
    task_type = task.get("task_type", "CURRENT_PERIOD_SEARCH")
    return {
        "id": cid,
        "created_at": generated_at,
        "module": module,
        "year": task.get("year"),
        "month": task.get("month"),
        "task_type": task_type,
        "historical_mandate": task_type == "HISTORICAL_BACKFILL_REQUIRED",
        "title": item.get("title", ""),
        "link": item.get("link", ""),
        "published": item.get("published", ""),
        "source_id": feed.id,
        "source": feed.name,
        "source_category": feed.category,
        "source_domain": feed.domain,
        "confidence": score,
        "status": status,
        "risk_level": "yellow" if status == "VERIFIED_SOURCE_CANDIDATE" else "green",
        "match_reasons": reasons,
        "cashflow_scope": "ALL_APBN_APBD_RP1_TRACE",
        "summary": item.get("summary", "")[:500],
        "next_action": (
            "Backfill historis wajib: cek arsip resmi, duplikasi Gudang DB, nominal/periode, status verifikasi, lalu draft CSV/PR."
            if task_type == "HISTORICAL_BACKFILL_REQUIRED"
            else "Cek duplikasi Gudang DB, pastikan nominal/periode, tambah evidence resmi atau dua sumber independen, lalu buat draft CSV/PR."
        ),
        "publish_guard": "Tidak boleh menjadi data rill/final sebelum review dan evidence lolos policy.",
    }


def merge_candidates(new_items: list[dict], keep_existing: bool) -> list[dict]:
    if not keep_existing:
        return normalize_candidates(sorted(new_items, key=lambda item: str(item.get("created_at", "")), reverse=True)[:2000])
    old_payload = read_json(CANDIDATES_JSON, {"candidates": []})
    old_items = old_payload.get("candidates", [])
    by_id = {str(item.get("id")): item for item in old_items if item.get("id")}
    for item in new_items:
        by_id.setdefault(str(item["id"]), item)
    return normalize_candidates(sorted(by_id.values(), key=lambda item: str(item.get("created_at", "")), reverse=True)[:2000])


def normalize_candidates(candidates: list[dict]) -> list[dict]:
    for item in candidates:
        item.setdefault("task_type", "CURRENT_PERIOD_SEARCH")
        item.setdefault("historical_mandate", item.get("task_type") == "HISTORICAL_BACKFILL_REQUIRED")
    return candidates


def write_candidates_csv(candidates: list[dict]) -> None:
    CANDIDATES_CSV.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "id",
        "created_at",
        "module",
        "year",
        "month",
        "task_type",
        "historical_mandate",
        "title",
        "link",
        "published",
        "source",
        "source_category",
        "confidence",
        "status",
        "cashflow_scope",
        "next_action",
    ]
    with CANDIDATES_CSV.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for item in candidates:
            writer.writerow({field: item.get(field, "") for field in fields})


def summarize(candidates: list[dict], new_count: int, failures: list[dict], generated_at: str, tasks: list[dict]) -> dict:
    by_module: dict[str, int] = {}
    by_status: dict[str, int] = {}
    by_source: dict[str, int] = {}
    high_confidence = 0
    historical_candidates = 0
    for item in candidates:
        by_module[item.get("module", "unknown")] = by_module.get(item.get("module", "unknown"), 0) + 1
        by_status[item.get("status", "unknown")] = by_status.get(item.get("status", "unknown"), 0) + 1
        by_source[item.get("source", "unknown")] = by_source.get(item.get("source", "unknown"), 0) + 1
        if int(item.get("confidence") or 0) >= 80:
            high_confidence += 1
        if item.get("historical_mandate"):
            historical_candidates += 1
    top = sorted(candidates, key=lambda item: int(item.get("confidence") or 0), reverse=True)[:15]
    historical_tasks = [task for task in tasks if task.get("task_type") == "HISTORICAL_BACKFILL_REQUIRED"]
    current_tasks = [task for task in tasks if task.get("task_type", "CURRENT_PERIOD_SEARCH") == "CURRENT_PERIOD_SEARCH"]
    public_submissions = read_json(PUBLIC_SUBMISSIONS_JSON, {})
    public_count = int(public_submissions.get("count") or 0) if isinstance(public_submissions, dict) else 0
    return {
        "generated_at": generated_at,
        "engine": "MR_AI_PENGAWAS_ORCHESTRATOR",
        "purpose": "Patroli 24/7 untuk menemukan kandidat DB uang rakyat dari sumber publik dan resmi.",
        "cashflow_scope": "ALL_APBN_APBD_RP1_TRACE",
        "mode": "scheduled_github_actions_or_backend_worker",
        "autonomous_tool_mandate": AUTONOMOUS_TOOL_MANDATE,
        "daily_flow_controller": DAILY_FLOW_CONTROLLER,
        "public_db_upload_policy": PUBLIC_DB_UPLOAD_POLICY,
        "public_submission_queue": {
            "file": "gudang-db/_queue/public_submissions.json",
            "count": public_count,
            "default_status": "DRAFT_PUBLIC_SUBMISSION",
            "hardcoded_rule": "Masukan publik dari upload/paste wajib masuk queue audit AI, bukan ditelan pasif.",
        },
        "safety": {
            "auto_publish_final_data": False,
            "write_public_claims_directly": False,
            "token_in_html": False,
            "required_before_rill": "sumber resmi atau dua sumber independen, nominal/periode jelas, dan review manusia/AI policy guard",
            "hunter_autonomy": "AI Hunter boleh mencari, membuat draft, dedupe, dan mapping otomatis 24/7; guard hanya mencegah klaim final palsu.",
        },
        "historical_backfill_policy": {
            "hardcoded": True,
            "target_years": 15,
            "minimum_required_years": 10,
            "mandate": "Tim AI Pengumpul DB wajib mencari dan mengisi data historis 10-15 tahun ke belakang ke Gudang DB.",
            "html_policy": "HTML publik hanya menampilkan tahun/bulan berjalan; periode lama diarahkan ke Gudang DB.",
        },
        "task_counts": {
            "total": len(tasks),
            "current_period": len(current_tasks),
            "historical_backfill": len(historical_tasks),
        },
        "queue_files": {
            "json": "gudang-db/_queue/ai_pengawas_candidates.json",
            "csv": "gudang-db/_queue/ai_pengawas_candidates.csv",
        },
        "total_candidates": len(candidates),
        "new_candidates_this_run": new_count,
        "high_confidence_candidates": high_confidence,
        "historical_backfill_candidates": historical_candidates,
        "public_submissions_pending_audit": public_count,
        "by_module": dict(sorted(by_module.items())),
        "by_status": dict(sorted(by_status.items())),
        "by_source": dict(sorted(by_source.items(), key=lambda item: item[1], reverse=True)[:20]),
        "top_candidates": top,
        "failures": failures[:20],
    }


def write_report(status: dict) -> None:
    lines = [
        "# AI Pengawas Orchestrator 24/7 Report",
        "",
        f"Generated: {status['generated_at']} Asia/Jakarta",
        "",
        "## Scope",
        "",
        "- Misi: setiap aliran APBN/APBD, sampai Rp 1, harus bisa ditelusuri ke program, instansi, vendor, bukti, dan status verifikasi.",
        "- Output otomatis masuk draft queue, bukan data final.",
        "- Data final tetap harus lolos policy guard, evidence, dan review.",
        "- Hardcode: Tim AI Pengumpul DB wajib mencari 10-15 tahun data historis; tahun berjalan boleh on-process.",
        "- Hardcode: semua tool/sumber yang tersedia wajib dimanfaatkan mandiri 24/7; tidak boleh berhenti di queue tanpa promosi draft.",
        "- Upload DB Rakyat: link, Excel, Word, PDF, catatan/noted, CSV, dan teks diterima sebagai DRAFT_PUBLIC_SUBMISSION.",
        "- Validitas awal >= 50 wajib masuk audit queue Gudang DB sesegera mungkin; < 40 wajib audit ketat dan fake dikick.",
        f"- Koordinator harian: {status['daily_flow_controller']['name']} mengatur urutan build, validasi, patrol, dan sinkron dashboard.",
        "",
        "## Status",
        "",
        f"- Total candidates: {status['total_candidates']}",
        f"- New candidates this run: {status['new_candidates_this_run']}",
        f"- High confidence candidates: {status['high_confidence_candidates']}",
        f"- Historical backfill tasks: {status['task_counts']['historical_backfill']}",
        f"- Historical backfill candidates: {status['historical_backfill_candidates']}",
        f"- Public submissions pending audit: {status['public_submissions_pending_audit']}",
        f"- Autonomous mode: {status['autonomous_tool_mandate']['mode']}",
        f"- Artificial source limit: {not status['autonomous_tool_mandate']['no_artificial_limit']}",
        "",
        "## Daily Flow Controller",
        "",
        f"- ID: {status['daily_flow_controller']['id']}",
        f"- Mission: {status['daily_flow_controller']['mission']}",
        "- Hardcoded tasks:",
    ]
    for task in status["daily_flow_controller"]["daily_hardcoded_tasks"]:
        lines.append(f"  - {task}")
    lines.extend([
        "",
        "## Autonomous Tool Mandate",
        "",
        f"- Mode: {status['autonomous_tool_mandate']['mode']}",
        f"- Rule: {status['autonomous_tool_mandate']['principle']}",
        "- Tools/sources wajib dipakai:",
    ])
    for tool in status["autonomous_tool_mandate"]["must_use_available_tools"]:
        lines.append(f"  - {tool}")
    lines.extend([
        "",
        "## Upload DB Rakyat Policy",
        "",
        f"- Entry status: {status['public_db_upload_policy']['entry_status']}",
        f"- Accepted inputs: {', '.join(status['public_db_upload_policy']['accepted_inputs'])}",
        f"- Minimum queue score: {status['public_db_upload_policy']['triage_thresholds']['minimum_queue_score']}%",
        f"- Reject/audit ketat below: {status['public_db_upload_policy']['triage_thresholds']['reject_below_score']}%",
        f"- Page update rule: {status['public_db_upload_policy']['page_update_rule']}",
        f"- Public queue: {status['public_submission_queue']['file']} ({status['public_submission_queue']['count']} pending)",
    ])
    lines.extend([
        "",
        "## Module Coverage",
        "",
    ])
    for module, count in status["by_module"].items():
        lines.append(f"- {module}: {count}")
    lines.extend(["", "## Safety Guard", ""])
    for key, value in status["safety"].items():
        lines.append(f"- {key}: {value}")
    REPORT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


def run() -> int:
    generated_at = now_jakarta().isoformat(timespec="seconds")
    keep_existing = "--reset-queue" not in sys.argv
    tasks = read_json(TASKS, [])
    if not tasks:
        print("No AI agent tasks found. Run pre_github_readiness.py --write first.")
        return 0
    feeds = load_feeds()
    existing_ids = existing_candidate_ids() if keep_existing else set()
    new_candidates: list[dict] = []
    failures: list[dict] = []

    for feed in feeds[:MAX_FEEDS_PER_RUN]:
        if len(new_candidates) >= MAX_TOTAL_NEW:
            break
        try:
            items = parse_feed(fetch_url(feed.feed_url))
        except Exception as exc:
            failures.append({"source": feed.name, "feed_url": feed.feed_url, "error": str(exc)[:200]})
            continue
        for item in items:
            for task in tasks:
                score, reasons = score_item(task, feed, item)
                if score < 62:
                    continue
                candidate = make_candidate(task, feed, item, score, reasons, generated_at)
                if candidate["id"] in existing_ids:
                    continue
                existing_ids.add(candidate["id"])
                new_candidates.append(candidate)
                if len(new_candidates) >= MAX_TOTAL_NEW:
                    break
            if len(new_candidates) >= MAX_TOTAL_NEW:
                break
        time.sleep(0.2)

    all_candidates = merge_candidates(new_candidates, keep_existing)
    payload = {
        "generated_at": generated_at,
        "purpose": "Draft queue hasil patroli AI Pengawas. Jangan dipublish sebagai data final sebelum review.",
        "cashflow_scope": "ALL_APBN_APBD_RP1_TRACE",
        "candidates": all_candidates,
    }
    status = summarize(all_candidates, len(new_candidates), failures, generated_at, tasks)
    write_json(CANDIDATES_JSON, payload)
    write_candidates_csv(all_candidates)
    write_json(STATUS_JSON, status)
    write_report(status)
    print(f"AI Pengawas Orchestrator wrote {len(new_candidates)} new candidates, {len(all_candidates)} total.")
    print(f"Queue: {CANDIDATES_JSON.relative_to(ROOT)}")
    print(f"Status: {STATUS_JSON.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(run())
