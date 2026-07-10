"""budget reconcile commands."""

from __future__ import annotations

from datetime import date

import click

from budget.reconciliation.reconciler import Reconciler
from budget.sheets.client import SheetsClient


@click.group()
def reconcile_cmd():
    """Reconcile transactions against a bank statement."""


@reconcile_cmd.command("start")
@click.option("--account", "-a", required=True)
@click.option("--statement-date", required=True, help="Statement end date YYYY-MM-DD")
@click.option("--opening", required=True, type=float, help="Opening balance on statement")
@click.option("--closing", required=True, type=float, help="Closing balance on statement")
def start(account: str, statement_date: str, opening: float, closing: float) -> None:
    """Start a new reconciliation session."""
    stmt_date = date.fromisoformat(statement_date)
    client = SheetsClient()
    reconciler = Reconciler(client)
    stmt = reconciler.start(account, stmt_date, opening, closing)
    click.echo(f"Started reconciliation: {stmt.statement_id}")
    click.echo(f"  Opening: {opening:.2f}  Closing: {closing:.2f}")


@reconcile_cmd.command("mark")
@click.option("--txn-id", required=True)
@click.option("--statement-id", required=True)
def mark(txn_id: str, statement_id: str) -> None:
    """Mark a transaction as cleared against a statement."""
    client = SheetsClient()
    reconciler = Reconciler(client)
    ok = reconciler.mark_cleared(txn_id, statement_id)
    if ok:
        click.echo(f"Marked {txn_id} as cleared on {statement_id}")
    else:
        click.echo(f"Transaction {txn_id} not found.", err=True)
        raise SystemExit(1)


@reconcile_cmd.command("status")
@click.option("--statement-id", required=True)
def status(statement_id: str) -> None:
    """Show current reconciliation status and difference."""
    client = SheetsClient()
    reconciler = Reconciler(client)
    st = reconciler.status(statement_id)
    if "error" in st:
        click.echo(f"Error: {st['error']}", err=True)
        raise SystemExit(1)

    diff = st["difference"]
    diff_str = f"{diff:+.2f}"
    click.echo(f"Statement:       {st['statement_id']}")
    click.echo(f"Account:         {st['account_id']}")
    click.echo(f"Date:            {st['statement_date']}")
    click.echo(f"Opening balance: {st['opening_balance']:.2f}")
    click.echo(f"Closing balance: {st['closing_balance']:.2f}")
    click.echo(f"Cleared balance: {st['cleared_balance']:.2f}")
    click.echo(f"Difference:      {diff_str}  {'OK' if diff == 0 else '*** UNRECONCILED ***'}")


@reconcile_cmd.command("suggest")
@click.option("--statement-id", required=True)
def suggest(statement_id: str) -> None:
    """List uncleared transactions that could be marked cleared."""
    client = SheetsClient()
    reconciler = Reconciler(client)
    candidates = reconciler.suggest_uncleared(statement_id)
    if not candidates:
        click.echo("No uncleared transactions found for this statement period.")
        return
    click.echo(f"{'TXN_ID':<18}  {'DATE':<12}  {'AMOUNT':>10}  DESCRIPTION")
    click.echo("-" * 70)
    for c in candidates:
        click.echo(
            f"{c['txn_id']:<18}  {c['txn_date']:<12}  {c['amount']:>10.2f}  {c['description']}"
        )


@reconcile_cmd.command("complete")
@click.option("--statement-id", required=True)
def complete(statement_id: str) -> None:
    """Finalize a reconciliation (difference must be 0)."""
    client = SheetsClient()
    reconciler = Reconciler(client)
    try:
        reconciler.complete(statement_id)
        click.echo(f"Reconciliation {statement_id} completed successfully.")
    except ValueError as e:
        click.echo(f"Error: {e}", err=True)
        raise SystemExit(1)
