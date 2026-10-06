from __future__ import annotations

import argparse
import csv
import hashlib
import json
import time
import urllib.request
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
FEEDS = ROOT / "gudang-db" / "master" / "master_source_feeds.csv"
OUT = ROOT / "dashboard" / "source_health.json"
TASKS_OUT = ROOT / "dashboard" / "source_recovery_tasks.json"

OFFICIAL_PREFIX = "OFFICIAL_"
USER_AGENT = "MonitoringRakyat-SourceHealth/2.0 (+https://github.com/MonitoringUangRakyat/monitoring-rakyat)"


def read_rows():
    with FEEDS.open("r", encoding="utf-8-sig", newline="") as handle:
        return [{str(k or "").strip(): str(v or "").strip() for k, v in row.items()} for row in csv.DictReader(handle)]


def probe(url: str, timeout: int = 12) -> tuple[str, int, str]:
    start = time.monotonic()
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "*/*"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:
            response.read(2048)
            ms = int((time.monotonic() - start) * 1000)
            return ("LIVE" if 200 <= response.status < 400 else "DEGRADED", ms, "")
    except Exception as exc:
        ms = int((time.monotonic() - start) * 1000)
        return "UNAVAILABLE", ms, f"{type(exc).__name__}: {exc}"[:500]


def structural_status(row: dict[str, str]) -> str:
    category = row.get("kategori", "").upper()
    url = row.get("feed_url", "").strip()
    if url:
        return "REGISTERED"
    if category.startswith(OFFICIAL_PREFIX):
        return "DISCOVERY_REQUIRED"
    return "NO_ENDPOINT"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--probe", action="store_true")
    args = parser.parse_args()
    now = datetime.now(ZoneInfo("Asia/Jakarta"))
    health, tasks = [], []
    for row in read_rows():
        status = structural_status(row)
        latency_ms = None
        error = ""
        if args.probe and row.get("feed_url"):
            status, latency_ms, error = probe(row["feed_url"])
        health.append({
            "source_id": row.get("id"), "source": row.get("nama_sumber"),
            "category": row.get("kategori"), "domain": row.get("domain"),
            "feed_url": row.get("feed_url"), "status": status,
            "checked_at": now.isoformat(timespec="seconds"), "latency_ms": latency_ms,
            "error_reason": error,
            "registry_fingerprint": hashlib.sha256("|".join(row.get(k, "") for k in ("id","domain","feed_url","kategori")).encode()).hexdigest()[:16],
        })
        if status in {"DISCOVERY_REQUIRED", "NO_ENDPOINT", "UNAVAILABLE", "DEGRADED"}:
            official = row.get("kategori", "").upper().startswith(OFFICIAL_PREFIX)
            tasks.append({
                "task": "resolve_source_endpoint" if not row.get("feed_url") else "recover_source",
                "source_id": row.get("id"), "source": row.get("nama_sumber"),
                "domain": row.get("domain"), "category": row.get("kategori"),
                "priority": "CRITICAL" if official else "HIGH", "status": "ACTIVE",
                "reason": status, "search_query_template": row.get("search_query_template"),
                "next_retry": (now + timedelta(hours=1 if official else 3)).isoformat(timespec="seconds"),
                "rule": "UNKNOWN/NO_ENDPOINT must become a task; never invent replacement data.",
            })
    payload = {
        "generated_at": now.isoformat(timespec="seconds"), "probe_enabled": args.probe,
        "sources": health,
        "counts": {s: sum(1 for x in health if x["status"] == s) for s in sorted({x["status"] for x in health})},
        "recovery_tasks": len(tasks),
    }
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    TASKS_OUT.write_text(json.dumps(tasks, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    print(f"Source health: {payload['counts']} | recovery_tasks={len(tasks)}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
