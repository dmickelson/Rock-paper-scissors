from datetime import date

import pytest

from budget.models import CategoryRule, Transaction
from budget.rules.engine import CategoryRulesEngine


def _txn(description: str, amount: float = -10.0) -> Transaction:
    return Transaction(
        txn_id="test",
        import_date=date.today(),
        txn_date=date.today(),
        account_id="chase",
        description=description,
        normalized_desc=description.upper(),
        amount=amount,
    )


def test_first_match_wins(basic_rules):
    engine = CategoryRulesEngine(basic_rules)
    txn = _txn("WHOLE FOODS MARKET")
    assert engine.categorize(txn) == "Groceries"


def test_trader_joes_matches_groceries(basic_rules):
    engine = CategoryRulesEngine(basic_rules)
    assert engine.categorize(_txn("TRADER JOE S 123")) == "Groceries"


def test_amazon_matches_shopping(basic_rules):
    engine = CategoryRulesEngine(basic_rules)
    assert engine.categorize(_txn("AMAZON.COM PRIME")) == "Shopping"


def test_netflix_matches_streaming(basic_rules):
    engine = CategoryRulesEngine(basic_rules)
    assert engine.categorize(_txn("NETFLIX.COM")) == "Streaming"


def test_no_match_returns_uncategorized(basic_rules):
    engine = CategoryRulesEngine(basic_rules)
    assert engine.categorize(_txn("RANDOM UNKNOWN VENDOR XYZ")) == "Uncategorized"


def test_amount_range_rule(basic_rules):
    engine = CategoryRulesEngine(basic_rules)
    assert engine.categorize(_txn("PAYROLL", amount=3200.0)) == "Income"


def test_inactive_rule_skipped():
    rules = [
        CategoryRule(rule_id=1, priority=10, category_name="Groceries",
                     field="normalized_desc", pattern=r"WHOLE FOODS",
                     match_type="regex", active=False),
    ]
    engine = CategoryRulesEngine(rules)
    assert engine.categorize(_txn("WHOLE FOODS")) == "Uncategorized"


def test_explain_shows_match(basic_rules):
    engine = CategoryRulesEngine(basic_rules)
    trace = engine.explain(_txn("WHOLE FOODS MARKET"))
    matched = [e for e in trace if e["matched"]]
    assert len(matched) == 1
    assert matched[0]["category"] == "Groceries"


def test_case_insensitive_match(basic_rules):
    engine = CategoryRulesEngine(basic_rules)
    assert engine.categorize(_txn("whole foods market")) == "Groceries"


def test_contains_match_type():
    rules = [
        CategoryRule(rule_id=1, priority=10, category_name="Coffee",
                     field="description", pattern="STARBUCKS",
                     match_type="contains", active=True),
    ]
    engine = CategoryRulesEngine(rules)
    assert engine.categorize(_txn("STARBUCKS #67890")) == "Coffee"
