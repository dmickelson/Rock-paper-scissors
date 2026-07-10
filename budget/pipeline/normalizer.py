"""Clean and normalize raw transaction descriptions and amounts."""

from __future__ import annotations

import re

# Noise tokens common across bank exports
_NOISE_PATTERNS = [
    r"\bPURCHASE\b",
    r"\bDEBIT\b",
    r"\bONLINE\b",
    r"\bPOS\b",
    r"\bCARD\b",
    r"\bPAYMENT\b",
    r"\bTRANSACTION\b",
    r"\bACH\b",
    r"#\d{4,}",          # reference numbers like #00012345
    r"\d{2}/\d{2}",      # embedded date fragments like 12/01
    r"\s{2,}",           # multiple spaces → single
]

_NOISE_RE = re.compile("|".join(_NOISE_PATTERNS), re.IGNORECASE)


def normalize_description(raw: str) -> str:
    cleaned = raw.upper().strip()
    cleaned = _NOISE_RE.sub(" ", cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned


def normalize_amount(amount: float, txn_type: str = "") -> float:
    """Ensure debits are negative and credits are positive.

    Some bank CSV exports provide separate debit/credit columns or use
    positive-only amounts with a type indicator. Pass txn_type='debit'
    to flip the sign when needed.
    """
    if txn_type.lower() in ("debit", "dr"):
        return -abs(amount)
    return amount
