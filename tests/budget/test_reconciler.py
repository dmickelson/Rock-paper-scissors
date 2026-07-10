from datetime import date
from unittest.mock import MagicMock, patch

import pytest

from budget.reconciliation.reconciler import Reconciler


def _make_client(txn_records=None, reconcile_records=None):
    client = MagicMock()
    client.get_all_records.side_effect = lambda sheet: (
        txn_records if "Transaction" in sheet else reconcile_records or []
    )
    client.find_row.return_value = 2
    return client


def test_start_creates_statement():
    client = _make_client()
    r = Reconciler(client)
    stmt = r.start("chase_checking", date(2025, 1, 31), 1000.0, 1500.0)
    assert stmt.statement_id == "chase_checking_2025-01-31"
    assert stmt.status == "in_progress"
    client.append_rows.assert_called_once()


def test_mark_cleared_calls_update():
    client = _make_client()
    r = Reconciler(client)
    ok = r.mark_cleared("abc123", "chase_checking_2025-01-31")
    assert ok is True
    assert client.update_cell.call_count == 3


def test_status_computes_difference():
    reconcile_records = [{
        "statement_id": "chase_2025-01",
        "account_id": "chase_checking",
        "statement_date": "2025-01-31",
        "opening_balance": "1000.00",
        "closing_balance": "1500.00",
        "status": "in_progress",
    }]
    txn_records = [
        {"account_id": "chase_checking", "cleared": "TRUE",
         "statement_id": "chase_2025-01", "amount": "300.00",
         "txn_date": "2025-01-15"},
        {"account_id": "chase_checking", "cleared": "TRUE",
         "statement_id": "chase_2025-01", "amount": "200.00",
         "txn_date": "2025-01-20"},
        {"account_id": "chase_checking", "cleared": "FALSE",
         "statement_id": "", "amount": "-50.00",
         "txn_date": "2025-01-25"},
    ]
    client = _make_client(txn_records, reconcile_records)
    r = Reconciler(client)
    st = r.status("chase_2025-01")
    assert st["cleared_balance"] == 1500.0  # 1000 + 300 + 200
    assert st["difference"] == 0.0


def test_complete_raises_on_nonzero_difference():
    reconcile_records = [{
        "statement_id": "chase_2025-01",
        "account_id": "chase_checking",
        "statement_date": "2025-01-31",
        "opening_balance": "1000.00",
        "closing_balance": "1500.00",
        "status": "in_progress",
    }]
    txn_records = []
    client = _make_client(txn_records, reconcile_records)
    r = Reconciler(client)
    with pytest.raises(ValueError, match="difference"):
        r.complete("chase_2025-01")
