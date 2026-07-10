"""Load CategoryRules and GmailPatterns from Google Sheets."""

from __future__ import annotations

from budget.models import Account, CategoryRule, GmailPattern
from budget.sheets import schema
from budget.sheets.client import SheetsClient


def _to_int(val, default: int = 0) -> int:
    try:
        return int(val)
    except (ValueError, TypeError):
        return default


def _to_float(val, default=None):
    try:
        return float(val)
    except (ValueError, TypeError):
        return default


def _to_bool(val) -> bool:
    if isinstance(val, bool):
        return val
    return str(val).strip().upper() in ("TRUE", "1", "YES")


def load_rules(client: SheetsClient) -> list[CategoryRule]:
    records = client.get_all_records(schema.CATEGORY_RULES)
    rules = []
    for r in records:
        try:
            rules.append(CategoryRule(
                rule_id=_to_int(r.get("rule_id", 0)),
                priority=_to_int(r.get("priority", 99)),
                category_name=str(r.get("category_name", "")).strip(),
                field=str(r.get("field", "normalized_desc")).strip(),
                pattern=str(r.get("pattern", "")).strip(),
                match_type=str(r.get("match_type", "regex")).strip(),
                amount_min=_to_float(r.get("amount_min")),
                amount_max=_to_float(r.get("amount_max")),
                active=_to_bool(r.get("active", True)),
                notes=str(r.get("notes", "")),
            ))
        except Exception:
            pass  # skip malformed rows silently
    return rules


def load_accounts(client: SheetsClient) -> list[Account]:
    records = client.get_all_records(schema.ACCOUNTS)
    accounts = []
    for r in records:
        try:
            from datetime import date
            od = r.get("opening_date", "")
            accounts.append(Account(
                account_id=str(r.get("account_id", "")).strip(),
                name=str(r.get("name", "")),
                institution=str(r.get("institution", "")),
                type=str(r.get("type", "checking")),
                currency=str(r.get("currency", "USD")),
                opening_balance=_to_float(r.get("opening_balance", 0.0)) or 0.0,
                opening_date=date.fromisoformat(od) if od else None,
                active=_to_bool(r.get("active", True)),
                gmail_sender_pattern=str(r.get("gmail_sender_pattern", "")),
                csv_date_format=str(r.get("csv_date_format", "%m/%d/%Y")),
                csv_column_map=str(r.get("csv_column_map", "{}")),
            ))
        except Exception:
            pass
    return accounts


def load_gmail_patterns(client: SheetsClient) -> list[GmailPattern]:
    records = client.get_all_records(schema.GMAIL_PATTERNS)
    patterns = []
    for r in records:
        try:
            patterns.append(GmailPattern(
                pattern_id=_to_int(r.get("pattern_id", 0)),
                institution=str(r.get("institution", "")),
                sender_regex=str(r.get("sender_regex", "")),
                subject_regex=str(r.get("subject_regex", "")),
                amount_regex=str(r.get("amount_regex", "")),
                merchant_regex=str(r.get("merchant_regex", "")),
                date_regex=str(r.get("date_regex", "")),
                account_id=str(r.get("account_id", "")),
                active=_to_bool(r.get("active", True)),
            ))
        except Exception:
            pass
    return patterns
