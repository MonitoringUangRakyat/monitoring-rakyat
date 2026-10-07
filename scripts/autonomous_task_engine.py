from __future__ import annotations

import hashlib
import json
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
SOURCES = [
    ROOT / "dashboard" / "source_recovery_tasks.json",
    ROOT / "dashboard" / "official_source_recovery_tasks.json",
    ROOT / "dashboard" / "evidence_recovery_tasks.json",
    ROOT / "dashboard" / "backfill_tasks.json",
    ROOT / "gudang-db" / "_queue" / "official_evidence_candidates.json",
    ROOT / "dashboard" / "ai_agent_tasks.json",
]
OUT = ROOT / "dashboard" / "autonomous_tasks.json"
STATUS = ROOT / "dashboard" / "autonomy_status.json"
PREV = OUT

def _load(path: Path):
    if not path.exists():
        return []
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, dict):
        for key in ("tasks", "items", "queue", "candidates"):
            if isinstance(value.get(key), list):
                return value[key]
    return []

def _id(task: dict) -> str:
    if task.get("task_id"):
        return str(task["task_id"])
    if task.get("candidate_id"):
        return "TASK-" + str(task["candidate_id"])
    basis = "|".join(str(task.get(k, "")) for k in ("task", "task_type", "source_id", "module", "year", "record_ref", "reason", "url"))
    return "AUTO-" + hashlib.sha256(basis.encode()).hexdigest()[:16].upper()

def _normalize(item: dict, previous: dict, now: datetime) -> dict:
    out = dict(item)
    if out.get("candidate_id") and not out.get("task"):
        out["task"] = "validate_official_evidence_candidate"
        out["priority"] = "CRITICAL" if int(out.get("source_authority", 0) or 0) >= 100 else "HIGH"
        out["status"] = "ACTIVE"
        out["reason"] = "OFFICIAL_SOURCE_CANDIDATE_REQUIRES_DOCUMENT_VALIDATION"
    tid = _id(out)
    out["task_id"] = tid
    out.setdefault("status", "ACTIVE")
    out.setdefault("priority", "MEDIUM")
    out["attempt_count"] = int(previous.get(tid, {}).get("attempt_count", out.get("attempt_count", 0) or 0))
    out.setdefault("max_attempts", 8)
    out.setdefault("created_at", previous.get(tid, {}).get("created_at", now.isoformat(timespec="seconds")))
    out["updated_at"] = now.isoformat(timespec="seconds")
    if "next_retry" not in out and "next_run_at" not in out:
        delay = min(24, 2 ** min(out["attempt_count"], 4))
        out["next_run_at"] = (now + timedelta(hours=delay)).isoformat(timespec="seconds")
    return out

def main() -> int:
    now = datetime.now(ZoneInfo("Asia/Jakarta"))
    previous = {_id(x): x for x in _load(PREV)}
    merged = {}
    for source in SOURCES:
        for raw in _load(source):
            item = _normalize(raw, previous, now)
            merged[item["task_id"]] = item
    tasks = sorted(merged.values(), key=lambda x: ({"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}.get(str(x.get("priority", "MEDIUM")).upper(), 9), x["task_id"]))
    dead = [x for x in tasks if int(x.get("attempt_count", 0)) >= int(x.get("max_attempts", 8))]
    for x in dead:
        x["status"] = "DEAD_LETTER"
    OUT.write_text(json.dumps(tasks, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    payload = {
        "generated_at": now.isoformat(timespec="seconds"),
        "policy": "EVERY_UNKNOWN_AND_EVIDENCE_GAP_BECOMES_A_TASK",
        "total": len(tasks),
        "active": sum(1 for x in tasks if x.get("status") not in {"DONE", "DEAD_LETTER"}),
        "dead_letter": len(dead),
        "critical": sum(1 for x in tasks if str(x.get("priority", "")).upper() == "CRITICAL"),
        "by_task": {name: sum(1 for x in tasks if x.get("task") == name) for name in sorted({str(x.get("task", "UNKNOWN")) for x in tasks})},
        "sources": [str(p.relative_to(ROOT)) for p in SOURCES],
    }
    STATUS.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Autonomous task engine: {payload}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
