from pathlib import Path

import pytest

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture
def sample_csv():
    return FIXTURES / "sample.csv"


@pytest.fixture
def sample_ofx():
    return FIXTURES / "sample.ofx"


@pytest.fixture
def sample_email_text():
    return (FIXTURES / "sample_email.txt").read_text()


@pytest.fixture
def chase_account():
    from budget.models import Account
    return Account(
        account_id="chase_checking",
        name="Chase Checking",
        institution="Chase",
        type="checking",
        csv_date_format="%m/%d/%Y",
    )


@pytest.fixture
def basic_rules():
    from budget.models import CategoryRule
    return [
        CategoryRule(rule_id=1, priority=10, category_name="Groceries",
                     field="normalized_desc", pattern=r"WHOLE\s*FOODS|TRADER\s*JOE",
                     match_type="regex", active=True),
        CategoryRule(rule_id=2, priority=20, category_name="Shopping",
                     field="normalized_desc", pattern=r"AMAZON",
                     match_type="regex", active=True),
        CategoryRule(rule_id=3, priority=30, category_name="Streaming",
                     field="normalized_desc", pattern=r"NETFLIX|HULU|DISNEY",
                     match_type="regex", active=True),
        CategoryRule(rule_id=4, priority=40, category_name="Gas",
                     field="normalized_desc", pattern=r"SHELL|CHEVRON|EXXON|BP\b",
                     match_type="regex", active=True),
        CategoryRule(rule_id=5, priority=50, category_name="Coffee",
                     field="normalized_desc", pattern=r"STARBUCKS|DUNKIN",
                     match_type="regex", active=True),
        CategoryRule(rule_id=6, priority=90, category_name="Income",
                     field="amount", pattern="", match_type="amount_range",
                     amount_min=1.0, amount_max=None, active=True),
    ]
