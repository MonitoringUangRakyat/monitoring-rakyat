from __future__ import annotations

import hashlib
import json
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "config" / "official_source_registry.json"
OUT = ROOT / "dashboard" / "official_source_discovery.json"
TASKS = ROOT / "dashboard" / "official_source_recovery_tasks.json"
UA = "MonitoringRakyat-OfficialDiscovery/1.0 (+https://github.com/MonitoringUangRakyat/monitoring-rakyat)"
MAX_READ = 256 * 1024

def _allowed(url: str, domains: list[str]) -> bool:
    host = (urllib.parse.urlparse(url).hostname or "").lower()
    return any(host == d.lower() or host.endswith("." + d.lower()) for d in domains)

def probe(url: str, domains: list[str], timeout: int = 15) -> dict:
    if not _allowed(url, domains):
        return {"url": url, "status": "REJECTED_DOMAIN", "http_status": None, "latency_ms": None}
    started = time.monotonic()
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "text/html,application/xhtml+xml,*/*;q=0.8"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as res:
            raw = res.read(MAX_READ)
            latency = int((time.monotonic() - started) * 1000)
            ctype = (res.headers.get("content-type") or "").lower()
            return {"url": res.geturl(), "status": "LIVE" if 200 <= res.status < 400 else "DEGRADED", "http_status": res.status, "latency_ms": latency, "content_type": ctype, "content_hash": hashlib.sha256(raw).hexdigest(), "bytes_sampled": len(raw)}
    except urllib.error.HTTPError as exc:
        return {"url": url, "status": "DEGRADED", "http_status": exc.code, "latency_ms": int((time.monotonic()-started)*1000), "error": str(exc)[:300]}
    except Exception as exc:
        return {"url": url, "status": "DOWN", "http_status": None, "latency_ms": int((time.monotonic()-started)*1000), "error": f"{type(exc).__name__}: {exc}"[:300]}

def main() -> int:
    now = datetime.now(ZoneInfo("Asia/Jakarta"))
    cfg = json.loads(REGISTRY.read_text(encoding="utf-8"))
    results, tasks = [], []
    for src in cfg["sources"]:
        attempts = [probe(u, src["domains"]) for u in src["candidate_urls"]]
        live = next((a for a in attempts if a["status"] == "LIVE"), None)
        status = "LIVE" if live else ("DEGRADED" if any(a["status"]=="DEGRADED" for a in attempts) else "DOWN")
        results.append({"source_id": src["source_id"], "name": src["name"], "authority": src["authority"], "status": status, "selected_url": live["url"] if live else None, "attempts": attempts, "checked_at": now.isoformat(timespec="seconds")})
        if not live:
            tasks.append({"task_id": f"OFFICIAL-{src['source_id']}", "task": "recover_official_source", "source_id": src["source_id"], "source": src["name"], "status": "ACTIVE", "priority": "CRITICAL", "reason": status, "next_retry": (now + timedelta(hours=1)).isoformat(timespec="seconds"), "candidate_urls": src["candidate_urls"], "rule": "Official source unavailable -> retry/recover/escalate. Never substitute AI-generated facts."})
    payload = {"generated_at": now.isoformat(timespec="seconds"), "policy": "OFFICIAL_SOURCE_FIRST", "counts": {s: sum(1 for x in results if x["status"] == s) for s in ("LIVE","DEGRADED","DOWN")}, "sources": results}
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    TASKS.write_text(json.dumps(tasks, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Official discovery: {payload['counts']} recovery_tasks={len(tasks)}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
