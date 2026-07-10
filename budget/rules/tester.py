"""Debug utility: test a description string against all loaded rules."""

from __future__ import annotations

from datetime import date

from budget.models import Transaction
from budget.rules.engine import CategoryRulesEngine


def test_description(engine: CategoryRulesEngine, description: str) -> None:
    """Print which rule matches the given description string."""
    dummy = Transaction(
        txn_id="test",
        import_date=date.today(),
        txn_date=date.today(),
        account_id="test",
        description=description,
        normalized_desc=description.upper(),
        amount=-1.0,
    )
    trace = engine.explain(dummy)
    print(f"\nTesting: {description!r}\n")
    for entry in trace:
        status = "MATCH" if entry["matched"] else "     "
        print(
            f"  [{status}] priority={entry['priority']:>3}  "
            f"{entry['category']:<20}  {entry['match_type']:<12}  "
            f"field={entry['field']:<15}  pattern={entry['pattern']!r}"
        )
        if entry["matched"]:
            print(f"\n  => Category: {entry['category']}")
            return
    print("\n  => Category: Uncategorized (no rules matched)")
