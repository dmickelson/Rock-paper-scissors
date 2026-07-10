"""Transaction deduplication against existing Sheets data."""

from __future__ import annotations

import hashlib
import json
from datetime import date
from typing import Optional


def make_txn_id(account_id: str, txn_date: date, amount: float, description: str) -> str:
    """Stable hash of the four fields that uniquely identify a transaction."""
    payload = f"{account_id}|{txn_date.isoformat()}|{amount:.2f}|{description}"
    return hashlib.sha256(payload.encode()).hexdigest()[:16]


def extract_fitid(raw_data: str) -> Optional[str]:
    """Pull fitid out of a JSON raw_data blob if present."""
    try:
        data = json.loads(raw_data)
        return data.get("fitid")
    except (json.JSONDecodeError, AttributeError):
        return None


def extract_gmail_message_id(raw_data: str) -> Optional[str]:
    """Pull Gmail message_id out of a JSON raw_data blob if present."""
    try:
        data = json.loads(raw_data)
        return data.get("gmail_message_id")
    except (json.JSONDecodeError, AttributeError):
        return None


class Deduplicator:
    def __init__(self, existing_ids: set[str], existing_raw: list[str] | None = None) -> None:
        self._ids = existing_ids
        # Build fitid and gmail_message_id lookup sets from existing raw_data
        self._fitids: set[str] = set()
        self._gmail_ids: set[str] = set()
        for raw in (existing_raw or []):
            fitid = extract_fitid(raw)
            if fitid:
                self._fitids.add(fitid)
            gmail_id = extract_gmail_message_id(raw)
            if gmail_id:
                self._gmail_ids.add(gmail_id)

    def is_duplicate(self, txn_id: str, raw_data: str = "") -> bool:
        if txn_id in self._ids:
            return True
        fitid = extract_fitid(raw_data)
        if fitid and fitid in self._fitids:
            return True
        gmail_id = extract_gmail_message_id(raw_data)
        if gmail_id and gmail_id in self._gmail_ids:
            return True
        return False

    def register(self, txn_id: str, raw_data: str = "") -> None:
        self._ids.add(txn_id)
        fitid = extract_fitid(raw_data)
        if fitid:
            self._fitids.add(fitid)
        gmail_id = extract_gmail_message_id(raw_data)
        if gmail_id:
            self._gmail_ids.add(gmail_id)
