from __future__ import annotations

import csv
import hashlib
import json
import os
import re
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo


ROOT = Path(__file__).resolve().parents[1]
QUEUE_JSON = ROOT / "gudang-db" / "_queue" / "public_submissions.json"
QUEUE_CSV = ROOT / "gudang-db" / "_queue" / "public_submissions.csv"
STATUS_JSON = ROOT / "dashboard" / "public_submission_status.json"

DEFAULT_REPO = "MonitoringUangRakyat/monitoring-rakyat"
USER_AGENT = "MonitoringRakyat-PublicSubmissionImporter/1.0"
MODULE_KEYWORDS = {
    "korupsi": ["korupsi", "kpk", "kejaksaan", "putusan", "tersangka", "kerugian negara"],
    "vendor": ["vendor", "kontrak", "tender", "lpse", "sirup", "pengadaan"],
    "pajak": ["pajak", "djp", "tax", "ppn", "pph"],
    "sda": ["sda", "tambang", "minerba", "royalti", "pnbp", "hutan", "perikanan"],
    "bea_cukai": ["bea cukai", "cukai", "djbc", "kepabeanan"],
    "bansos": ["bansos", "bantuan sosial", "dtks"],
    "akuntansi": ["apbn", "apbd", "realisasi", "belanja", "pagu", "anggaran"],
}


def now_jakarta() -> str:
    return datetime.now(ZoneInfo("Asia/Jakarta")).isoformat(timespec="seconds")


def write_json(path: Path, payload) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def read_json(path: Path, default):
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError:
        return default


def fetch_json(url: str, token: str | None) -> object:
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": USER_AGENT,
        "X-GitHub-Api-Version": "2022-11-28",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))


def normalize_text(value: str) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def issue_id(issue: dict) -> str:
    raw = f"{issue.get('html_url', '')}|{issue.get('updated_at', '')}|{issue.get('title', '')}"
    return "MR-PUBLIC-" + hashlib.sha256(raw.encode("utf-8", "ignore")).hexdigest()[:16].upper()


def anonymous_ref(submission_id: str) -> str:
    return f"ANON_PUBLIC_SUBMISSION:{submission_id}"


def detect_module(text: str) -> str:
    lower = text.lower()
    scores: dict[str, int] = {}
    for module, keywords in MODULE_KEYWORDS.items():
        scores[module] = sum(1 for keyword in keywords if keyword in lower)
    best, score = max(scores.items(), key=lambda item: item[1])
    return best if score else "public_submission"


def detect_year(text: str) -> str:
    match = re.search(r"(19\d{2}|20\d{2})", text)
    return match.group(1) if match else ""


def validity_score(text: str) -> int:
    lower = text.lower()
    score = 20
    if re.search(r"https?://", text):
        score += 25
    if re.search(r"(19\d{2}|20\d{2})", text):
        score += 10
    if re.search(r"\b(rp|idr|anggaran|kontrak|pagu|realisasi|kerugian|miliar|triliun|juta)\b", lower):
        score += 15
    if any(word in lower for word in ("bpk", "kpk", "lkpp", "sirup", "lpse", "putusan", "kemenkeu", "kejaksaan")):
        score += 20
    if any(word in lower for word in ("pdf", ".pdf", ".csv", ".xlsx", ".docx", "attachment", "uploaded")):
        score += 10
    return max(0, min(100, score))


def status_from_score(score: int) -> str:
    if score >= 50:
        return "DRAFT_PUBLIC_SUBMISSION_READY_FOR_AUDIT_QUEUE"
    if score >= 40:
        return "PUBLIC_SUBMISSION_NEEDS_SOURCE_PATROL"
    return "PUBLIC_SUBMISSION_STRICT_AUDIT_OR_REJECT"


def normalize_issue(issue: dict, generated_at: str) -> dict:
    title = normalize_text(issue.get("title", ""))
    body = str(issue.get("body", "") or "").replace("\r\n", "\n").strip()
    text = f"{title}\n{body}"
    score = validity_score(text)
    submission_id = issue_id(issue)
    return {
        "id": submission_id,
        "issue_number": "ANON",
        "title": title,
        "issue_url": anonymous_ref(submission_id),
        "source_ref": anonymous_ref(submission_id),
        "privacy_rule": "GitHub username/issue URL tidak dipublish; kontribusi publik disimpan sebagai referensi anonim.",
        "created_at": issue.get("created_at", ""),
        "updated_at": issue.get("updated_at", ""),
        "captured_at": generated_at,
        "module": detect_module(text),
        "year": detect_year(text),
        "status": status_from_score(score),
        "entry_status": "DRAFT_PUBLIC_SUBMISSION",
        "validity_score": score,
        "audit_rule": ">=50 masuk audit queue Gudang DB; 40-49 source patrol; <40 audit ketat/fake kick.",
        "body_preview": body[:60000],
    }


def normalize_dispatch_payload(payload: dict, generated_at: str) -> dict:
    file_names = " ".join(
        normalize_text(item.get("name", ""))
        for item in payload.get("files", [])
        if isinstance(item, dict)
    )
    body = "\n".join([normalize_text(payload.get("paste_preview", "")), file_names]).strip()
    text = f"{payload.get('module', '')}\n{payload.get('period', '')}\n{body}"
    score = validity_score(text)
    raw_id = normalize_text(payload.get("id", ""))
    submission_id = raw_id or "MR-PUBLIC-" + hashlib.sha256(text.encode("utf-8", "ignore")).hexdigest()[:16].upper()
    return {
        "id": submission_id,
        "issue_number": "ANON",
        "title": f"Anonymous public upload {normalize_text(payload.get('module', 'BELUM_DIPILIH'))}",
        "issue_url": anonymous_ref(submission_id),
        "source_ref": anonymous_ref(submission_id),
        "privacy_rule": "Identitas pengirim tidak dipublish; intake anonim hanya memakai ID kontribusi.",
        "created_at": normalize_text(payload.get("submitted_at", "")),
        "updated_at": normalize_text(payload.get("submitted_at", "")),
        "captured_at": generated_at,
        "module": detect_module(text),
        "year": detect_year(text),
        "status": status_from_score(score),
        "entry_status": "DRAFT_PUBLIC_SUBMISSION",
        "validity_score": score,
        "audit_rule": ">=50 masuk audit queue Gudang DB; 40-49 source patrol; <40 audit ketat/fake kick.",
        "body_preview": body[:60000],
    }


def dispatch_candidates(generated_at: str) -> list[dict]:
    if os.environ.get("GITHUB_EVENT_NAME") != "repository_dispatch":
        return []
    event_path = os.environ.get("GITHUB_EVENT_PATH")
    if not event_path:
        return []
    try:
        event = json.loads(Path(event_path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []
    if event.get("action") != "public_submission":
        return []
    payload = event.get("client_payload")
    if not isinstance(payload, dict):
        return []
    return [normalize_dispatch_payload(payload, generated_at)]


def is_public_submission_issue(issue: dict) -> bool:
    labels = issue.get("labels") or []
    label_names = {
        str(item.get("name", "")).strip().lower()
        for item in labels
        if isinstance(item, dict)
    }
    title = normalize_text(issue.get("title", "")).lower()
    body = normalize_text(issue.get("body", "")).lower()
    markers = (
        "[upload db rakyat]",
        "upload/paste netizen",
        "draft_public_submission",
        "tombol upload data base publik",
    )
    return "public-submission" in label_names or any(marker in title or marker in body for marker in markers)


def fetch_public_issues(repo: str, token: str | None) -> list[dict]:
    query = urllib.parse.urlencode({"state": "open", "per_page": "100"})
    url = f"https://api.github.com/repos/{repo}/issues?{query}"
    payload = fetch_json(url, token)
    if not isinstance(payload, list):
        return []
    return [
        item
        for item in payload
        if isinstance(item, dict)
        and "pull_request" not in item
        and is_public_submission_issue(item)
    ]


def write_queue(candidates: list[dict], generated_at: str, repo: str, input_present: bool, note: str) -> None:
    payload = {
        "generated_at": generated_at,
        "source": "anonymous public intake endpoint / repository_dispatch",
        "repo": repo,
        "input_present": input_present,
        "count": len(candidates),
        "default_status": "DRAFT_PUBLIC_SUBMISSION",
        "hardcoded_rule": "Masukan publik anonim tidak ditelan pasif; setiap repository_dispatch public_submission masuk queue audit AI dan dipetakan ke Gudang DB.",
        "privacy_rule": "Kontribusi publik tidak boleh memakai GitHub Issue fallback karena nama akun pengirim akan tampil. Semua rujukan publik memakai ANON_PUBLIC_SUBMISSION.",
        "note": note,
        "candidates": candidates,
    }
    write_json(QUEUE_JSON, payload)
    QUEUE_CSV.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "id",
        "issue_number",
        "title",
        "issue_url",
        "module",
        "year",
        "entry_status",
        "status",
        "validity_score",
        "updated_at",
        "audit_rule",
    ]
    with QUEUE_CSV.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for item in candidates:
            writer.writerow({field: item.get(field, "") for field in fields})
    write_json(
        STATUS_JSON,
        {
            "generated_at": generated_at,
            "repo": repo,
            "input_present": input_present,
            "public_submissions_captured": len(candidates),
            "queue_json": "gudang-db/_queue/public_submissions.json",
            "queue_csv": "gudang-db/_queue/public_submissions.csv",
            "note": note,
        },
    )


def main() -> int:
    generated_at = now_jakarta()
    repo = os.environ.get("GITHUB_REPOSITORY") or DEFAULT_REPO
    candidates = dispatch_candidates(generated_at)
    if not candidates and QUEUE_JSON.exists():
        existing = read_json(QUEUE_JSON, {})
        candidates = existing.get("candidates") if isinstance(existing, dict) else []
        if not isinstance(candidates, list):
            candidates = []
        input_present = bool(candidates)
        note = "No new anonymous public-intake dispatch submissions; retained existing anonymized queue."
    else:
        input_present = bool(candidates)
        note = (
            f"Captured {len(candidates)} anonymous public-intake dispatch submissions."
            if candidates
            else "No anonymous public-intake dispatch submissions captured."
        )
    write_queue(candidates, generated_at, repo, input_present, note)
    print(note)
    print(f"Public submissions written: {len(candidates)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
