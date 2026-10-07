from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Mapping

# Public aggregation is DEFAULT DENY.
# Candidate/draft/review states may live in Gudang DB, but may not affect public totals.
PUBLISHABLE_STATUSES = {
    "VERIFIED",
    "VERIFIED_SOURCE",
    "RILL_CURRENT_PERIOD",
    "TEMUAN_AUDIT",
    "PUTUSAN",
    "INKRACHT",
    "INKRAH",
}

BLOCKED_MARKERS = (
    "DRAFT",
    "REVIEW",
    "UNVERIFIED",
    "CANDIDATE",
    "NEEDS_EVIDENCE",
    "NEEDS_MORE_EVIDENCE",
    "NEEDS_OFFICIAL_EVIDENCE",
    "NEEDS_VERIFICATION",
    "AI_CLASSIFIED",
    "PATROL_PENDING",
    "SEARCH_REQUIRED",
    "UNKNOWN",
    "PENDING",
    "REJECTED",
    "RETRACTED",
    "DISPUTED",
)

STATUS_KEYS = (
    "status_verifikasi",
    "status",
    "status_hukum",
    "status_audit",
    "status_investigasi",
    "status_tindak_lanjut",
    "aksi",
)

SOURCE_KEYS = (
    "sumber",
    "source",
    "sumber_perhitungan",
    "evidence",
    "dokumen",
    "link",
    "link_referensi",
    "link_ref_ma",
    "link_ref_kpk",
    "link_ref_kejaksaan",
    "link_ref_bpk",
    "putusan_sumber",
    "sumber_bpk",
    "sumber_kpk",
    "putusan_ma",
    "kejaksaan",
    "lkpp",
    "no_bukti",
)

LOSS_ALIASES = (
    "kerugian",
    "nilai_kerugian",
    "kerugian_diakibatkan",
    "total_kerugian",
)

RECOVERY_ALIASES = (
    "recovery",
    "dikembalikan",
    "dikembalikan_ke_negara",
    "asset_recovery",
)

MONEY_HINT_KEYS = (
    *LOSS_ALIASES,
    *RECOVERY_ALIASES,
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
    "belanja",
    "anggaran_apbn",
    "nilai_kontrak",
    "total_anggaran",
)


@dataclass(frozen=True)
class PublicationDecision:
    allowed: bool
    reason: str
    status: str
    source: str


def normalized(row: Mapping[str, object]) -> dict[str, str]:
    return {
        str(k or "").strip().lower(): str(v or "").strip()
        for k, v in row.items()
    }


def _status_values(row: Mapping[str, object]) -> list[str]:
    lower = normalized(row)
    values = []
    for key in STATUS_KEYS:
        value = lower.get(key, "").strip()
        if value:
            values.append(value.upper())
    return values


def source_value(row: Mapping[str, object]) -> str:
    lower = normalized(row)
    for key in SOURCE_KEYS:
        value = lower.get(key, "").strip()
        if value:
            return value
    return ""


def publication_decision(
    row: Mapping[str, object],
    *,
    require_source: bool = True,
) -> PublicationDecision:
    statuses = _status_values(row)
    joined = " | ".join(statuses)

    # A blocking marker anywhere wins. This prevents a generic legal status
    # from accidentally overriding AI_HUNTER_DRAFT_REVIEW.
    for value in statuses:
        if any(marker in value for marker in BLOCKED_MARKERS):
            return PublicationDecision(False, "blocked_status", joined, source_value(row))

    explicit = next((s for s in statuses if s in PUBLISHABLE_STATUSES), "")
    if not explicit:
        return PublicationDecision(False, "no_explicit_publishable_status", joined, source_value(row))

    source = source_value(row)
    if require_source and not source:
        return PublicationDecision(False, "missing_source", joined, "")

    return PublicationDecision(True, "publishable", joined, source)


def is_publishable_record(row: Mapping[str, object], *, require_source: bool = True) -> bool:
    return publication_decision(row, require_source=require_source).allowed


def parse_money(value: object) -> float:
    if value is None:
        return 0.0
    if isinstance(value, (int, float)):
        return float(value)

    text = str(value).strip().lower()
    if not text:
        return 0.0

    multiplier = 1
    if "triliun" in text or re.search(r"\bt\b", text):
        multiplier = 1_000_000_000_000
    elif "miliar" in text or re.search(r"\bm\b", text):
        multiplier = 1_000_000_000
    elif "juta" in text or "jt" in text:
        multiplier = 1_000_000

    match = re.search(r"-?\d[\d.,]*", text.replace("rp", "").replace("idr", ""))
    if not match:
        return 0.0

    raw = match.group(0)
    if "," in raw and re.search(r",\d{1,2}$", raw):
        raw = raw.replace(".", "").replace(",", ".")
    else:
        raw = raw.replace(".", "").replace(",", "")
    try:
        return float(raw) * multiplier
    except ValueError:
        return 0.0


def first_money(row: Mapping[str, object], aliases: tuple[str, ...]) -> float:
    """Treat aliases as the same semantic field; never sum aliases together."""
    lower = normalized(row)
    for key in aliases:
        value = lower.get(key)
        if value is not None and str(value).strip():
            return parse_money(value)
    return 0.0


def loss_amount(row: Mapping[str, object]) -> float:
    return first_money(row, LOSS_ALIASES)


def recovery_amount(row: Mapping[str, object]) -> float:
    return first_money(row, RECOVERY_ALIASES)


def has_money(row: Mapping[str, object]) -> bool:
    lower = normalized(row)
    return any(str(lower.get(key, "")).strip() for key in MONEY_HINT_KEYS)


def has_source(row: Mapping[str, object]) -> bool:
    return bool(source_value(row))
