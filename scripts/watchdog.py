from __future__ import annotations

import argparse
import json
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "dashboard" / "watchdog_status.json"
GATE = ROOT / "dashboard" / "promotion_gate.json"
CHECKS = {
    "dashboard_summary": (ROOT/"dashboard/dashboard_summary.json", 2),
    "publication_gate": (ROOT/"dashboard/publication_gate_status.json", 2),
    "source_health": (ROOT/"dashboard/source_health.json", 4),
    "official_source_discovery": (ROOT/"dashboard/official_source_discovery.json", 4),
    "autonomy_status": (ROOT/"dashboard/autonomy_status.json", 4),
}

def json_time(path: Path):
    try: data=json.loads(path.read_text(encoding="utf-8"))
    except Exception: return None
    for key in ("generated_at","checked_at"):
        value=data.get(key)
        if value:
            try: return datetime.fromisoformat(str(value).replace("Z","+00:00"))
            except Exception: pass
    return datetime.fromtimestamp(path.stat().st_mtime, tz=ZoneInfo("Asia/Jakarta"))

def main() -> int:
    parser=argparse.ArgumentParser(); parser.add_argument("--strict",action="store_true"); args=parser.parse_args()
    now=datetime.now(ZoneInfo("Asia/Jakarta")); failures=[]; checks={}
    for name,(path,max_hours) in CHECKS.items():
        if not path.exists():
            checks[name]={"status":"MISSING","path":str(path.relative_to(ROOT))}; failures.append(f"{name}:missing"); continue
        ts=json_time(path); stale = ts is None or (now - ts.astimezone(ZoneInfo("Asia/Jakarta"))) > timedelta(hours=max_hours)
        checks[name]={"status":"STALE" if stale else "OK","timestamp":ts.isoformat() if ts else None,"max_age_hours":max_hours}
        if stale: failures.append(f"{name}:stale")
    pub=ROOT/"dashboard/publication_gate_status.json"
    if pub.exists():
        try:
            if json.loads(pub.read_text(encoding="utf-8")).get("status") != "PASS": failures.append("publication_gate:not_pass")
        except Exception: failures.append("publication_gate:unreadable")
    stop=bool(failures)
    payload={"generated_at":now.isoformat(timespec="seconds"),"status":"STOP_PROMOTION" if stop else "HEALTHY","failures":failures,"checks":checks}
    OUT.write_text(json.dumps(payload,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    GATE.write_text(json.dumps({"generated_at":payload["generated_at"],"allow_promotion":not stop,"reason":failures or ["all_watchdog_checks_pass"]},ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(payload["status"], failures)
    return 1 if args.strict and stop else 0

if __name__=="__main__":
    raise SystemExit(main())
