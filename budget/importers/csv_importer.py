"""CSV transaction importer with per-bank column mapping."""

from __future__ import annotations

import csv
import hashlib
import json
from datetime import date, datetime
from pathlib import Path
from typing import Optional

from budget.importers.base import AbstractImporter
from budget.models import Account, Transaction
from budget.pipeline.deduplicator import make_txn_id
from budget.pipeline.normalizer import normalize_amount, normalize_description


# Default column name aliases used to map diverse bank CSV headers → canonical names
DEFAULT_ALIASES: dict[str, list[str]] = {
    "date": ["date", "transaction date", "trans date", "posted date", "txn date"],
    "post_date": ["post date", "posting date", "settlement date"],
    "description": [
        "description", "memo", "payee", "merchant", "transaction description",
        "name", "details",
    ],
    "amount": ["amount", "transaction amount"],
    "debit": ["debit", "withdrawals", "withdrawal", "debit amount"],
    "credit": ["credit", "deposits", "deposit", "credit amount"],
}


def _find_column(headers: list[str], aliases: list[str]) -> Optional[str]:
    """Return the first header that matches any alias (case-insensitive)."""
    lower_headers = {h.lower().strip(): h for h in headers}
    for alias in aliases:
        if alias.lower() in lower_headers:
            return lower_headers[alias.lower()]
    return None


def _parse_amount(debit_str: str, credit_str: str, amount_str: str) -> float:
    """Resolve debit/credit/amount columns into a signed float."""
    def clean(s: str) -> str:
        return s.replace(",", "").replace("$", "").replace("(", "-").replace(")", "").strip()

    if amount_str:
        return float(clean(amount_str))
    debit = float(clean(debit_str)) if debit_str.strip() else 0.0
    credit = float(clean(credit_str)) if credit_str.strip() else 0.0
    return credit - debit  # credit positive, debit negative


class CsvImporter(AbstractImporter):
    def parse(self, source: Path) -> list[Transaction]:
        col_map: dict = self.account.get_column_map()
        date_fmt = self.account.csv_date_format

        transactions = []
        with open(source, newline="", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            if reader.fieldnames is None:
                return []
            headers = list(reader.fieldnames)

            # Build resolved column → header mapping
            def resolve(canonical: str) -> Optional[str]:
                if canonical in col_map and col_map[canonical] in headers:
                    return col_map[canonical]
                return _find_column(headers, DEFAULT_ALIASES.get(canonical, []))

            col_date = resolve("date")
            col_post = resolve("post_date")
            col_desc = resolve("description")
            col_amount = resolve("amount")
            col_debit = resolve("debit")
            col_credit = resolve("credit")

            if not col_date or not col_desc:
                raise ValueError(
                    f"Cannot find required columns (date, description) in {source}. "
                    f"Headers: {headers}"
                )

            for row in reader:
                raw_date_str = row.get(col_date, "").strip()
                if not raw_date_str:
                    continue
                try:
                    txn_date = datetime.strptime(raw_date_str, date_fmt).date()
                except ValueError:
                    continue

                post_date_str = row.get(col_post, "").strip() if col_post else ""
                post_date: Optional[date] = None
                if post_date_str:
                    try:
                        post_date = datetime.strptime(post_date_str, date_fmt).date()
                    except ValueError:
                        pass

                description = row.get(col_desc, "").strip()
                raw_amount = row.get(col_amount, "") if col_amount else ""
                raw_debit = row.get(col_debit, "") if col_debit else ""
                raw_credit = row.get(col_credit, "") if col_credit else ""

                amount = _parse_amount(raw_debit, raw_credit, raw_amount)
                txn_id = make_txn_id(self.account.account_id, txn_date, amount, description)

                transactions.append(Transaction(
                    txn_id=txn_id,
                    import_date=date.today(),
                    txn_date=txn_date,
                    post_date=post_date,
                    account_id=self.account.account_id,
                    description=description,
                    normalized_desc=normalize_description(description),
                    amount=amount,
                    source="csv",
                    raw_data=json.dumps(dict(row)),
                ))

        return transactions
