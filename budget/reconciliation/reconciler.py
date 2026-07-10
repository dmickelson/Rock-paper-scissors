"""Reconciliation workflow: start → mark cleared → status → complete."""

from __future__ import annotations

from datetime import date
from typing import Optional

from budget.models import ReconciliationStatement, Transaction
from budget.sheets import schema
from budget.sheets.client import SheetsClient


def _to_bool(val) -> bool:
    if isinstance(val, bool):
        return val
    return str(val).strip().upper() in ("TRUE", "1", "YES")


def _to_float(val, default: float = 0.0) -> float:
    try:
        return float(val)
    except (ValueError, TypeError):
        return default


class Reconciler:
    def __init__(self, client: SheetsClient) -> None:
        self._client = client

    def start(
        self,
        account_id: str,
        statement_date: date,
        opening_balance: float,
        closing_balance: float,
    ) -> ReconciliationStatement:
        statement_id = f"{account_id}_{statement_date.isoformat()}"
        stmt = ReconciliationStatement(
            statement_id=statement_id,
            account_id=account_id,
            statement_date=statement_date,
            opening_balance=opening_balance,
            closing_balance=closing_balance,
            status="in_progress",
        )
        self._client.append_rows(schema.RECONCILIATION, [stmt.to_row()])
        return stmt

    def mark_cleared(self, txn_id: str, statement_id: str) -> bool:
        """Mark a transaction as cleared. Returns True if found and updated."""
        row = self._client.find_row(schema.TRANSACTIONS, "txn_id", txn_id)
        if row is None:
            return False
        cols = schema.TRANSACTION_COLUMNS
        cleared_col = cols.index("cleared") + 1
        date_col = cols.index("reconcile_date") + 1
        stmt_col = cols.index("statement_id") + 1
        self._client.update_cell(schema.TRANSACTIONS, row, cleared_col, True)
        self._client.update_cell(schema.TRANSACTIONS, row, date_col, date.today().isoformat())
        self._client.update_cell(schema.TRANSACTIONS, row, stmt_col, statement_id)
        return True

    def status(self, statement_id: str) -> dict:
        """Compute cleared balance and difference for a statement."""
        records = self._client.get_all_records(schema.RECONCILIATION)
        stmt_record = next(
            (r for r in records if r.get("statement_id") == statement_id), None
        )
        if stmt_record is None:
            return {"error": f"Statement {statement_id} not found"}

        account_id = str(stmt_record.get("account_id", ""))
        closing_balance = _to_float(stmt_record.get("closing_balance", 0))
        opening_balance = _to_float(stmt_record.get("opening_balance", 0))
        stmt_date = date.fromisoformat(str(stmt_record.get("statement_date", date.today())))

        txn_records = self._client.get_all_records(schema.TRANSACTIONS)
        cleared_sum = sum(
            _to_float(r.get("amount", 0))
            for r in txn_records
            if r.get("account_id") == account_id
            and _to_bool(r.get("cleared", False))
            and r.get("statement_id") == statement_id
        )
        cleared_balance = opening_balance + cleared_sum
        difference = round(closing_balance - cleared_balance, 2)

        return {
            "statement_id": statement_id,
            "account_id": account_id,
            "statement_date": stmt_date.isoformat(),
            "opening_balance": opening_balance,
            "closing_balance": closing_balance,
            "cleared_balance": cleared_balance,
            "difference": difference,
            "status": stmt_record.get("status", "in_progress"),
        }

    def complete(self, statement_id: str) -> bool:
        """Finalize a reconciliation. Returns True if difference is 0."""
        st = self.status(statement_id)
        if "error" in st:
            raise ValueError(st["error"])
        if st["difference"] != 0.0:
            raise ValueError(
                f"Cannot complete: difference is {st['difference']:.2f}. "
                "All transactions must be cleared first."
            )
        row = self._client.find_row(schema.RECONCILIATION, "statement_id", statement_id)
        if row is None:
            return False
        cols = schema.RECONCILIATION_COLUMNS
        self._client.update_cell(
            schema.RECONCILIATION, row, cols.index("status") + 1, "reconciled"
        )
        self._client.update_cell(
            schema.RECONCILIATION, row, cols.index("reconciled_date") + 1,
            date.today().isoformat()
        )
        self._client.update_cell(
            schema.RECONCILIATION, row, cols.index("cleared_balance") + 1,
            st["cleared_balance"]
        )
        self._client.update_cell(
            schema.RECONCILIATION, row, cols.index("difference") + 1, 0.0
        )
        return True

    def suggest_uncleared(self, statement_id: str) -> list[dict]:
        """Return uncleared transactions for this account/period as reconcile candidates."""
        st = self.status(statement_id)
        if "error" in st:
            return []
        account_id = st["account_id"]
        stmt_date = date.fromisoformat(st["statement_date"])

        txn_records = self._client.get_all_records(schema.TRANSACTIONS)
        candidates = []
        for r in txn_records:
            if r.get("account_id") != account_id:
                continue
            if _to_bool(r.get("cleared", False)):
                continue
            try:
                txn_date = date.fromisoformat(str(r.get("txn_date", "")))
            except ValueError:
                continue
            if txn_date <= stmt_date:
                candidates.append({
                    "txn_id": r.get("txn_id"),
                    "txn_date": str(txn_date),
                    "description": r.get("description"),
                    "amount": _to_float(r.get("amount", 0)),
                    "category": r.get("category"),
                })
        return sorted(candidates, key=lambda x: x["txn_date"])
