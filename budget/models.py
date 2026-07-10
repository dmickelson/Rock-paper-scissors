from __future__ import annotations

import json
import re
from datetime import date
from typing import Optional

from pydantic import BaseModel, PrivateAttr, model_validator


class Transaction(BaseModel):
    txn_id: str
    import_date: date
    txn_date: date
    post_date: Optional[date] = None
    account_id: str
    description: str
    normalized_desc: str = ""
    amount: float
    category: str = "Uncategorized"
    subcategory: str = ""
    tags: str = ""
    memo: str = ""
    cleared: bool = False
    reconcile_date: Optional[date] = None
    statement_id: str = ""
    source: str = "manual"
    raw_data: str = ""

    def to_row(self) -> list:
        return [
            self.txn_id,
            self.import_date.isoformat(),
            self.txn_date.isoformat(),
            self.post_date.isoformat() if self.post_date else "",
            self.account_id,
            self.description,
            self.normalized_desc,
            self.amount,
            self.category,
            self.subcategory,
            self.tags,
            self.memo,
            self.cleared,
            self.reconcile_date.isoformat() if self.reconcile_date else "",
            self.statement_id,
            self.source,
            self.raw_data,
        ]

    @classmethod
    def columns(cls) -> list[str]:
        return [
            "txn_id", "import_date", "txn_date", "post_date",
            "account_id", "description", "normalized_desc", "amount",
            "category", "subcategory", "tags", "memo",
            "cleared", "reconcile_date", "statement_id", "source", "raw_data",
        ]


class Account(BaseModel):
    account_id: str
    name: str
    institution: str
    type: str  # checking | savings | credit | investment
    currency: str = "USD"
    opening_balance: float = 0.0
    opening_date: Optional[date] = None
    active: bool = True
    gmail_sender_pattern: str = ""
    csv_date_format: str = "%m/%d/%Y"
    csv_column_map: str = "{}"  # JSON mapping bank col names → canonical

    def get_column_map(self) -> dict:
        return json.loads(self.csv_column_map) if self.csv_column_map else {}


class CategoryRule(BaseModel):
    rule_id: int
    priority: int
    category_name: str
    field: str  # description | normalized_desc | amount | account_id
    pattern: str
    match_type: str  # regex | contains | exact | amount_range
    amount_min: Optional[float] = None
    amount_max: Optional[float] = None
    active: bool = True
    notes: str = ""

    _compiled: Optional[re.Pattern] = PrivateAttr(default=None)

    def model_post_init(self, _context) -> None:
        if self.match_type == "regex" and self.pattern and self.active:
            self._compiled = re.compile(self.pattern, re.IGNORECASE)

    def matches(self, txn: Transaction) -> bool:
        if not self.active:
            return False
        field_value = getattr(txn, self.field, "")
        if self.match_type == "regex":
            if self._compiled is None:
                return False
            return bool(self._compiled.search(str(field_value)))
        elif self.match_type == "contains":
            return self.pattern.lower() in str(field_value).lower()
        elif self.match_type == "exact":
            return str(field_value).lower() == self.pattern.lower()
        elif self.match_type == "amount_range":
            amt = float(field_value) if field_value else 0.0
            lo = self.amount_min if self.amount_min is not None else float("-inf")
            hi = self.amount_max if self.amount_max is not None else float("inf")
            return lo <= amt <= hi
        return False


class GmailPattern(BaseModel):
    pattern_id: int
    institution: str
    sender_regex: str
    subject_regex: str = ""
    amount_regex: str
    merchant_regex: str = ""
    date_regex: str = ""
    account_id: str
    active: bool = True

    _sender_compiled: Optional[re.Pattern] = PrivateAttr(default=None)
    _subject_compiled: Optional[re.Pattern] = PrivateAttr(default=None)
    _amount_compiled: Optional[re.Pattern] = PrivateAttr(default=None)
    _merchant_compiled: Optional[re.Pattern] = PrivateAttr(default=None)
    _date_compiled: Optional[re.Pattern] = PrivateAttr(default=None)

    def model_post_init(self, _context) -> None:
        if self.sender_regex:
            self._sender_compiled = re.compile(self.sender_regex, re.IGNORECASE)
        if self.subject_regex:
            self._subject_compiled = re.compile(self.subject_regex, re.IGNORECASE)
        if self.amount_regex:
            self._amount_compiled = re.compile(self.amount_regex, re.IGNORECASE)
        if self.merchant_regex:
            self._merchant_compiled = re.compile(self.merchant_regex, re.IGNORECASE)
        if self.date_regex:
            self._date_compiled = re.compile(self.date_regex, re.IGNORECASE)

    def matches_email(self, sender: str, subject: str) -> bool:
        if not self.active:
            return False
        if self._sender_compiled and not self._sender_compiled.search(sender):
            return False
        if self._subject_compiled and not self._subject_compiled.search(subject):
            return False
        return True


class ReconciliationStatement(BaseModel):
    statement_id: str
    account_id: str
    statement_date: date
    opening_balance: float
    closing_balance: float
    cleared_balance: float = 0.0
    difference: float = 0.0
    status: str = "in_progress"  # in_progress | reconciled | discrepancy
    reconciled_date: Optional[date] = None

    def to_row(self) -> list:
        return [
            self.statement_id, self.account_id,
            self.statement_date.isoformat(),
            self.opening_balance, self.closing_balance,
            self.cleared_balance, self.difference,
            self.status,
            self.reconciled_date.isoformat() if self.reconciled_date else "",
        ]

    @classmethod
    def columns(cls) -> list[str]:
        return [
            "statement_id", "account_id", "statement_date",
            "opening_balance", "closing_balance",
            "cleared_balance", "difference", "status", "reconciled_date",
        ]
