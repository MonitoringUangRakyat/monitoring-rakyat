from __future__ import annotations

import hashlib
import html
import json
import urllib.parse
import urllib.request
from datetime import datetime
from html.parser import HTMLParser
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
DISCOVERY = ROOT / "dashboard" / "official_source_discovery.json"
REGISTRY = ROOT / "config" / "official_source_registry.json"
OUT = ROOT / "gudang-db" / "_queue" / "official_evidence_candidates.json"
STATUS = ROOT / "dashboard" / "official_evidence_hunter_status.json"
UA = "MonitoringRakyat-OfficialEvidenceHunter/1.0 (+https://github.com/MonitoringUangRakyat/monitoring-rakyat)"
MAX_READ = 512 * 1024
MAX_PER_SOURCE = 80

class LinkParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []
        self._href = None
        self._text = []
    def handle_starttag(self, tag, attrs):
        if tag.lower() == "a":
            self._href = dict(attrs).get("href")
            self._text = []
    def handle_data(self, data):
        if self._href is not None:
            self._text.append(data)
    def handle_endtag(self, tag):
        if tag.lower() == "a" and self._href is not None:
            self.links.append((self._href, " ".join(self._text).strip()))
            self._href = None
            self._text = []

def same_domain(url: str, domains: list[str]) -> bool:
    host = (urllib.parse.urlparse(url).hostname or "").lower()
    return any(host == d.lower() or host.endswith("." + d.lower()) for d in domains)

def fetch_html(url: str, domains: list[str]) -> tuple[str, str]:
    if not same_domain(url, domains):
        return "", "REJECTED_DOMAIN"
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "text/html,application/xhtml+xml"})
    try:
        with urllib.request.urlopen(req, timeout=20) as res:
            ctype = (res.headers.get("content-type") or "").lower()
            if "html" not in ctype:
                return "", "NON_HTML"
            raw = res.read(MAX_READ)
            return raw.decode("utf-8", errors="replace"), "OK"
    except Exception as exc:
        return "", f"ERROR:{type(exc).__name__}"

def main() -> int:
    now = datetime.now(ZoneInfo("Asia/Jakarta"))
    discovery = json.loads(DISCOVERY.read_text(encoding="utf-8")) if DISCOVERY.exists() else {"sources": []}
    registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
    cfg = {x["source_id"]: x for x in registry["sources"]}
    candidates = {}
    source_stats = []

    for state in discovery.get("sources", []):
        source_id = state.get("source_id")
        selected = state.get("selected_url")
        src = cfg.get(source_id)
        if not src or not selected or state.get("status") != "LIVE":
            source_stats.append({"source_id": source_id, "status": "SKIPPED_NOT_LIVE", "candidates": 0})
            continue
        body, fetch_status = fetch_html(selected, src["domains"])
        if not body:
            source_stats.append({"source_id": source_id, "status": fetch_status, "candidates": 0})
            continue
        parser = LinkParser()
        parser.feed(body)
        matched = 0
        keywords = [x.lower() for x in src.get("keywords", [])]
        for href, title in parser.links:
            if matched >= MAX_PER_SOURCE:
                break
            absolute = urllib.parse.urljoin(selected, href)
            parsed = urllib.parse.urlparse(absolute)
            if parsed.scheme not in {"http", "https"} or not same_domain(absolute, src["domains"]):
                continue
            clean_url = urllib.parse.urlunparse((parsed.scheme, parsed.netloc, parsed.path, parsed.params, parsed.query, ""))
            text = html.unescape(title).strip()
            haystack = f"{text} {clean_url}".lower()
            if keywords and not any(k in haystack for k in keywords):
                continue
            fingerprint = hashlib.sha256(f"{source_id}|{clean_url}|{text}".encode()).hexdigest()
            candidate_id = f"OFFEV-{fingerprint[:18].upper()}"
            candidates[candidate_id] = {
                "candidate_id": candidate_id,
                "source_id": source_id,
                "source_name": src["name"],
                "source_authority": src["authority"],
                "url": clean_url,
                "title": text[:500],
                "parent_url": selected,
                "captured_at": now.isoformat(timespec="seconds"),
                "candidate_hash": fingerprint,
                "status": "DRAFT_OFFICIAL_SOURCE_CANDIDATE",
                "promotion_allowed": False,
                "next_action": "Fetch/validate the referenced official document or page, bind citations/entities, then pass evidence gate.",
            }
            matched += 1
        source_stats.append({"source_id": source_id, "status": fetch_status, "candidates": matched})

    OUT.parent.mkdir(parents=True, exist_ok=True)
    ordered = sorted(candidates.values(), key=lambda x: (-int(x["source_authority"]), x["candidate_id"]))
    OUT.write_text(json.dumps(ordered, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    status = {
        "generated_at": now.isoformat(timespec="seconds"),
        "policy": "OFFICIAL_CANDIDATE_IS_STILL_A_CLAIM_UNTIL_DOCUMENT_VALIDATION",
        "total_candidates": len(ordered),
        "sources": source_stats,
    }
    STATUS.write_text(json.dumps(status, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Official evidence hunter: candidates={len(ordered)} sources={source_stats}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
