import json
from datetime import date

from budget.pipeline.deduplicator import Deduplicator, make_txn_id


def test_make_txn_id_stable():
    a = make_txn_id("chase", date(2025, 1, 15), -42.50, "WHOLE FOODS")
    b = make_txn_id("chase", date(2025, 1, 15), -42.50, "WHOLE FOODS")
    assert a == b


def test_make_txn_id_different_amount():
    a = make_txn_id("chase", date(2025, 1, 15), -42.50, "WHOLE FOODS")
    b = make_txn_id("chase", date(2025, 1, 15), -43.00, "WHOLE FOODS")
    assert a != b


def test_dedup_by_txn_id():
    dedup = Deduplicator({"abc123"})
    assert dedup.is_duplicate("abc123") is True
    assert dedup.is_duplicate("xyz999") is False


def test_dedup_by_fitid():
    raw = json.dumps({"fitid": "FIT001"})
    dedup = Deduplicator(set(), [raw])
    assert dedup.is_duplicate("new_id", json.dumps({"fitid": "FIT001"})) is True
    assert dedup.is_duplicate("new_id", json.dumps({"fitid": "FIT002"})) is False


def test_dedup_by_gmail_message_id():
    raw = json.dumps({"gmail_message_id": "MSG001"})
    dedup = Deduplicator(set(), [raw])
    assert dedup.is_duplicate("new_id", json.dumps({"gmail_message_id": "MSG001"})) is True


def test_register_prevents_future_duplicate():
    dedup = Deduplicator(set())
    assert dedup.is_duplicate("new_id") is False
    dedup.register("new_id")
    assert dedup.is_duplicate("new_id") is True
