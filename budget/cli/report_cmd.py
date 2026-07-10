"""budget report commands."""

from __future__ import annotations

import click

from budget.sheets import schema
from budget.sheets.client import SheetsClient


def _to_float(val, default: float = 0.0) -> float:
    try:
        return float(val)
    except (ValueError, TypeError):
        return default


@click.group()
def report_cmd():
    """View spending reports."""


@report_cmd.command("monthly")
@click.argument("year_month", metavar="YYYY-MM")
@click.option("--account", "-a", default="", help="Filter by account ID")
def monthly(year_month: str, account: str) -> None:
    """Show spending by category for YYYY-MM."""
    client = SheetsClient()
    txn_records = client.get_all_records(schema.TRANSACTIONS)

    totals: dict[str, float] = {}
    for r in txn_records:
        txn_date = str(r.get("txn_date", ""))
        if not txn_date.startswith(year_month):
            continue
        if account and r.get("account_id") != account:
            continue
        cat = str(r.get("category", "Uncategorized"))
        amt = _to_float(r.get("amount", 0))
        totals[cat] = totals.get(cat, 0.0) + amt

    if not totals:
        click.echo(f"No transactions found for {year_month}.")
        return

    click.echo(f"\nSpending for {year_month}" + (f" [{account}]" if account else "") + "\n")
    click.echo(f"{'CATEGORY':<30}  {'AMOUNT':>12}")
    click.echo("-" * 45)

    income_total = 0.0
    expense_total = 0.0
    for cat, amt in sorted(totals.items(), key=lambda x: x[1]):
        click.echo(f"{cat:<30}  {amt:>12.2f}")
        if amt >= 0:
            income_total += amt
        else:
            expense_total += amt

    click.echo("-" * 45)
    click.echo(f"{'Total Income':<30}  {income_total:>12.2f}")
    click.echo(f"{'Total Expenses':<30}  {expense_total:>12.2f}")
    click.echo(f"{'Net':<30}  {income_total + expense_total:>12.2f}")
