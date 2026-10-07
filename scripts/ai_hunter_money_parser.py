from __future__ import annotations
import re

UNITS = {
    "triliun": 1_000_000_000_000,
    "t": 1_000_000_000_000,
    "miliar": 1_000_000_000,
    "m": 1_000_000_000,
    "juta": 1_000_000,
    "jt": 1_000_000,
}

def _number(raw: str) -> float:
    raw = raw.strip()
    if "," in raw and re.search(r",\d{1,2}$", raw):
        raw = raw.replace(".", "").replace(",", ".")
    else:
        raw = raw.replace(".", "").replace(",", "")
    return float(raw)

def extract_money_mentions(text: object) -> list[int]:
    value = str(text or "").lower()
    out = []
    patterns = [
        re.compile(r"\b(?:rp|idr)\s*([0-9][0-9.,]*)\s*(triliun|miliar|juta|jt|t|m)?\b", re.I),
        re.compile(r"\b([0-9][0-9.,]*)\s*(triliun|miliar|juta|jt)\b", re.I),
    ]
    spans = set()
    for pattern in patterns:
        for match in pattern.finditer(value):
            if match.span() in spans:
                continue
            spans.add(match.span())
            raw = match.group(1)
            unit = (match.group(2) or "").lower()
            try:
                amount = _number(raw) * UNITS.get(unit, 1)
            except ValueError:
                continue
            if not unit and 1900 <= amount <= 2100:
                continue
            if amount > 0:
                out.append(round(amount))
    return out

def primary_money_mention(text: object) -> int:
    values = extract_money_mentions(text)
    return values[0] if values else 0
