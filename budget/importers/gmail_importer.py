"""Gmail transaction importer: search emails, parse amounts, label processed."""

from __future__ import annotations

import base64
import json
import re
from datetime import date, datetime, timedelta
from email import message_from_bytes
from typing import Optional

from budget.config import settings
from budget.importers.base import AbstractImporter
from budget.models import Account, GmailPattern, Transaction
from budget.pipeline.deduplicator import make_txn_id
from budget.pipeline.normalizer import normalize_description

IMPORTED_LABEL = "finance-imported"


class GmailImporter:
    def __init__(self, gmail_service, account: Account, patterns: list[GmailPattern]) -> None:
        self._svc = gmail_service
        self.account = account
        self._patterns = [p for p in patterns if p.account_id == account.account_id and p.active]

    def _get_or_create_label(self) -> str:
        """Return the Gmail label ID for IMPORTED_LABEL, creating it if needed."""
        labels_resp = self._svc.users().labels().list(userId="me").execute()
        for label in labels_resp.get("labels", []):
            if label["name"] == IMPORTED_LABEL:
                return label["id"]
        created = self._svc.users().labels().create(
            userId="me",
            body={"name": IMPORTED_LABEL, "labelListVisibility": "labelHide"},
        ).execute()
        return created["id"]

    def _search_messages(self, pattern: GmailPattern) -> list[dict]:
        lookback = settings.gmail_lookback_days
        query_parts = [f"newer_than:{lookback}d", f"-label:{IMPORTED_LABEL}"]
        if pattern.sender_regex:
            # Gmail search uses from: with exact addresses, not regex — we filter post-fetch
            raw_sender = re.sub(r"[\\^$.*+?()[\]{}|]", "", pattern.sender_regex)
            query_parts.append(f"from:{raw_sender}")
        if pattern.subject_regex:
            raw_subject = re.sub(r"[\\^$.*+?()[\]{}|]", "", pattern.subject_regex)
            query_parts.append(f"subject:{raw_subject}")

        query = " ".join(query_parts)
        result = self._svc.users().messages().list(userId="me", q=query).execute()
        return result.get("messages", [])

    @staticmethod
    def _extract_body(payload: dict) -> str:
        """Recursively extract text/plain body from Gmail message payload."""
        mime_type = payload.get("mimeType", "")
        if mime_type == "text/plain":
            data = payload.get("body", {}).get("data", "")
            if data:
                return base64.urlsafe_b64decode(data).decode("utf-8", errors="replace")
        for part in payload.get("parts", []):
            body = GmailImporter._extract_body(part)
            if body:
                return body
        return ""

    def _parse_email(self, msg_id: str, pattern: GmailPattern) -> Optional[Transaction]:
        msg = self._svc.users().messages().get(
            userId="me", id=msg_id, format="full"
        ).execute()

        headers = {h["name"].lower(): h["value"] for h in msg.get("payload", {}).get("headers", [])}
        sender = headers.get("from", "")
        subject = headers.get("subject", "")

        if not pattern.matches_email(sender, subject):
            return None

        body = self._extract_body(msg.get("payload", {}))
        full_text = f"{subject}\n{body}"

        if not pattern._amount_compiled:
            return None

        amount_match = pattern._amount_compiled.search(full_text)
        if not amount_match:
            return None

        amount_str = amount_match.group("amount").replace(",", "")
        try:
            amount = -abs(float(amount_str))  # spending is negative
        except ValueError:
            return None

        merchant = ""
        if pattern._merchant_compiled:
            m = pattern._merchant_compiled.search(full_text)
            if m:
                merchant = m.group("merchant").strip()

        txn_date = date.today()
        if pattern._date_compiled:
            d = pattern._date_compiled.search(full_text)
            if d:
                date_str = d.group("date")
                for fmt in ("%m/%d/%Y", "%Y-%m-%d", "%m-%d-%Y", "%d/%m/%Y"):
                    try:
                        txn_date = datetime.strptime(date_str, fmt).date()
                        break
                    except ValueError:
                        pass

        description = merchant or f"{pattern.institution} transaction"
        txn_id = make_txn_id(self.account.account_id, txn_date, amount, description)

        raw = json.dumps({
            "gmail_message_id": msg_id,
            "subject": subject,
            "sender": sender,
            "institution": pattern.institution,
        })

        return Transaction(
            txn_id=txn_id,
            import_date=date.today(),
            txn_date=txn_date,
            account_id=self.account.account_id,
            description=description,
            normalized_desc=normalize_description(description),
            amount=amount,
            source="gmail",
            raw_data=raw,
        )

    def import_transactions(self, dry_run: bool = False) -> list[Transaction]:
        label_id = None if dry_run else self._get_or_create_label()
        results: list[Transaction] = []

        for pattern in self._patterns:
            messages = self._search_messages(pattern)
            for msg_ref in messages:
                msg_id = msg_ref["id"]
                txn = self._parse_email(msg_id, pattern)
                if txn:
                    results.append(txn)
                    if not dry_run and label_id:
                        self._svc.users().messages().modify(
                            userId="me",
                            id=msg_id,
                            body={"addLabelIds": [label_id]},
                        ).execute()

        return results
