from __future__ import annotations

import csv
import json
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo


ROOT = Path(__file__).resolve().parents[1]
FEEDS = ROOT / "gudang-db" / "master" / "master_source_feeds.csv"
TASKS = ROOT / "dashboard" / "ai_agent_tasks.json"
OUT = ROOT / "dashboard" / "ai_agent_source_patrol.json"

KEYWORDS_BY_MODULE = {
    "akuntansi": ["APBN", "realisasi anggaran", "belanja negara"],
    "audit": ["temuan BPK", "audit", "kerugian negara"],
    "audittrail": ["audit pengadaan", "temuan audit", "tindak lanjut BPK"],
    "bea_cukai": ["bea cukai", "penyelundupan", "cukai ilegal", "kerugian negara"],
    "bumn": ["BUMN", "kerugian negara", "korupsi BUMN"],
    "korupsi": ["korupsi", "kerugian negara", "tersangka", "putusan"],
    "pajak": ["pajak", "DJP", "penggelapan pajak", "kerugian negara"],
    "parpol": ["dana parpol", "bantuan partai politik", "hibah organisasi"],
    "prog_daerah": ["APBD", "proyek daerah", "pengadaan daerah"],
    "prog_eksekutif": ["proyek kementerian", "pengadaan kementerian", "APBN"],
    "prog_legislatif": ["DPR", "DPRD", "anggaran legislatif"],
    "redflag": ["tender bermasalah", "proyek bermasalah", "red flag pengadaan"],
    "risknas": ["risiko korupsi", "kerugian negara", "pengadaan bermasalah"],
    "sda": ["tambang ilegal", "kehutanan", "perikanan", "SDA", "kerugian negara"],
    "vendor": ["vendor pengadaan", "pemenang tender", "LPSE", "SiRUP"],
}


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return [{str(k or "").strip(): str(v or "").strip() for k, v in row.items()} for row in csv.DictReader(handle)]


def read_json(path: Path):
    if not path.exists():
        return []
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> None:
    now = datetime.now(ZoneInfo("Asia/Jakarta"))
    feeds = read_csv(FEEDS)
    tasks = read_json(TASKS)
    active_modules = [task for task in tasks if task.get("status") == "SEARCH_REQUIRED"]
    patrol = []

    for task in active_modules:
        module = task["module"]
        year = task["year"]
        keywords = KEYWORDS_BY_MODULE.get(module, [module, "uang rakyat"])
        for feed in feeds:
            confidence = int(feed.get("confidence_awal") or 0)
            category = feed.get("kategori", "")
            if category == "COMMUNITY_TIP":
                continue
            if module in {"vendor", "prog_daerah", "prog_eksekutif", "prog_legislatif", "redflag"} and category not in {"OFFICIAL_PROCUREMENT", "MAINSTREAM_MEDIA", "AGGREGATOR_AI", "OFFICIAL_AUDIT"}:
                continue
            if module in {"korupsi", "bea_cukai", "bumn", "pajak", "sda", "audit", "risknas"} and category not in {"OFFICIAL_AUDIT", "OFFICIAL_ENFORCEMENT", "OFFICIAL_COURT", "OFFICIAL_BUDGET", "OFFICIAL_CUSTOMS", "MAINSTREAM_MEDIA", "AGGREGATOR_AI"}:
                continue
            for keyword in keywords[:3]:
                patrol.append(
                    {
                        "created_at": now.isoformat(timespec="seconds"),
                        "module": module,
                        "year": year,
                        "month": task["month"],
                        "source_id": feed["id"],
                        "source": feed["nama_sumber"],
                        "category": category,
                        "domain": feed["domain"],
                        "feed_url": feed.get("feed_url", ""),
                        "query": feed["search_query_template"].replace("{keyword}", keyword).replace("{tahun}", str(year)),
                        "confidence_awal": confidence,
                        "status": "PATROL_PENDING",
                        "next_action": "Validasi endpoint/query, ambil judul-link-tanggal, cross-check minimal dua sumber atau satu sumber resmi sebelum draft CSV.",
                    }
                )

    payload = {
        "generated_at": now.isoformat(timespec="seconds"),
        "purpose": "Daftar patroli proaktif Tim AI Agent untuk mencari DB kosong dari sumber resmi, media mainstream, dan agregator.",
        "rules": [
            "Media mainstream adalah sinyal awal 70-75, bukan bukti final tunggal.",
            "Sumber resmi/audit/putusan punya prioritas tertinggi.",
            "Nemesis hanya salah satu acuan red flag, bukan sumber tunggal.",
            "Semua hasil crawl masuk DRAFT_REVIEW sampai evidence lolos audit.",
        ],
        "patrol_count": len(patrol),
        "patrol": patrol,
    }
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {OUT.relative_to(ROOT)} with {len(patrol)} patrol items.")


if __name__ == "__main__":
    main()
