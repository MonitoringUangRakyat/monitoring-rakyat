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
    ROOT / "dashboard" / "ai_agent_tasks.json",
]
OUT = ROOT / "dashboard" / "autonomous_tasks.json"
STATUS = ROOT / "dashboard" / "autonomy_status.json"
PREV = OUT

def _load(path: Path):
    if not path.exists(): return []
    try: value = json.loads(path.read_text(encoding="utf-8"))
    except Exception: return []
    if isinstance(value, list): return value
    if isinstance(value, dict):
        for key in ("tasks","items","queue"):
            if isinstance(value.get(key), list): return value[key]
    return []

def _id(task: dict) -> str:
    if task.get("task_id"): return str(task["task_id"])
    basis = "|".join(str(task.get(k,"")) for k in ("task","task_type","source_id","module","year","record_ref","reason"))
    return "AUTO-" + hashlib.sha256(basis.encode()).hexdigest()[:16].upper()

def main() -> int:
    now = datetime.now(ZoneInfo("Asia/Jakarta"))
    previous = {_id(x): x for x in _load(PREV)}
    merged = {}
    for source in SOURCES:
        for task in _load(source):
            tid = _id(task)
            item = dict(task)
            item["task_id"] = tid
            item.setdefault("status", "ACTIVE")
            item.setdefault("priority", "MEDIUM")
            item.setdefault("attempt_count", int(previous.get(tid,{}).get("attempt_count", 0)))
            item.setdefault("max_attempts", 8)
            item.setdefault("created_at", previous.get(tid,{}).get("created_at", now.isoformat(timespec="seconds")))
            item["updated_at"] = now.isoformat(timespec="seconds")
            if "next_retry" not in item and "next_run_at" not in item:
                delay = min(24, 2 ** min(item["attempt_count"], 4))
                item["next_run_at"] = (now + timedelta(hours=delay)).isoformat(timespec="seconds")
            merged[tid] = item
    tasks = sorted(merged.values(), key=lambda x: ({"CRITICAL":0,"HIGH":1,"MEDIUM":2,"LOW":3}.get(str(x.get("priority","MEDIUM")).upper(), 9), x["task_id"]))
    dead = [x for x in tasks if int(x.get("attempt_count",0)) >= int(x.get("max_attempts",8))]
    for x in dead: x["status"] = "DEAD_LETTER"
    OUT.write_text(json.dumps(tasks, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    payload = {"generated_at": now.isoformat(timespec="seconds"), "policy": "EVERY_UNKNOWN_BECOMES_A_TASK", "total": len(tasks), "active": sum(1 for x in tasks if x.get("status") not in {"DONE","DEAD_LETTER"}), "dead_letter": len(dead), "critical": sum(1 for x in tasks if str(x.get("priority","")).upper()=="CRITICAL"), "sources": [str(p.relative_to(ROOT)) for p in SOURCES]}
    STATUS.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Autonomous task engine: {payload}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
