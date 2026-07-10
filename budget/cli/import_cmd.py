"""budget import command."""

from __future__ import annotations

from pathlib import Path

import click

from budget.config import settings
from budget.rules.engine import CategoryRulesEngine
from budget.rules.loader import load_accounts, load_gmail_patterns, load_rules
from budget.sheets.client import SheetsClient
from budget.pipeline.pipeline import ImportPipeline


def _get_client() -> SheetsClient:
    return SheetsClient()


def _get_engine(client: SheetsClient) -> CategoryRulesEngine:
    rules = load_rules(client)
    return CategoryRulesEngine(rules)


@click.group()
def import_cmd():
    """Import transactions from CSV, OFX/QFX, or Gmail."""


@import_cmd.command("file")
@click.option("--file", "-f", "filepath", required=True, type=click.Path(exists=True))
@click.option("--account", "-a", required=True, help="Account ID from the Accounts sheet")
@click.option("--dry-run", is_flag=True, help="Parse and categorize without writing to Sheets")
def import_file(filepath: str, account: str, dry_run: bool) -> None:
    """Import transactions from a CSV or OFX/QFX file."""
    path = Path(filepath)
    client = _get_client()
    engine = _get_engine(client)

    accounts = load_accounts(client)
    acct = next((a for a in accounts if a.account_id == account), None)
    if acct is None:
        click.echo(f"Account '{account}' not found in Accounts sheet.", err=True)
        raise SystemExit(1)

    suffix = path.suffix.lower()
    if suffix == ".csv":
        from budget.importers.csv_importer import CsvImporter
        importer = CsvImporter(acct)
    elif suffix in (".ofx", ".qfx"):
        from budget.importers.ofx_importer import OfxImporter
        importer = OfxImporter(acct)
    else:
        click.echo(f"Unsupported file type: {suffix}", err=True)
        raise SystemExit(1)

    transactions = importer.parse(path)
    pipeline = ImportPipeline(client, engine)
    result = pipeline.run(transactions, f"{suffix[1:]}:{path.name}", account, dry_run=dry_run)

    click.echo(
        f"{'[DRY RUN] ' if dry_run else ''}"
        f"Parsed {result.rows_parsed}, "
        f"imported {result.rows_imported}, "
        f"skipped {result.rows_skipped} duplicates"
    )
    if result.errors:
        for err in result.errors:
            click.echo(f"  ERROR: {err}", err=True)


@import_cmd.command("gmail")
@click.option("--account", "-a", required=True, help="Account ID to import Gmail transactions for")
@click.option("--dry-run", is_flag=True, help="Parse without writing to Sheets or labeling emails")
def import_gmail(account: str, dry_run: bool) -> None:
    """Import transactions from Gmail bank notification emails."""
    from googleapiclient.discovery import build
    from budget.auth.google_auth import get_credentials

    creds = get_credentials(settings.google_credentials_file, settings.google_token_file)
    gmail_svc = build("gmail", "v1", credentials=creds)

    client = _get_client()
    engine = _get_engine(client)

    accounts = load_accounts(client)
    acct = next((a for a in accounts if a.account_id == account), None)
    if acct is None:
        click.echo(f"Account '{account}' not found.", err=True)
        raise SystemExit(1)

    patterns = load_gmail_patterns(client)
    from budget.importers.gmail_importer import GmailImporter
    importer = GmailImporter(gmail_svc, acct, patterns)

    transactions = importer.import_transactions(dry_run=dry_run)
    pipeline = ImportPipeline(client, engine)
    result = pipeline.run(transactions, "gmail:inbox", account, dry_run=dry_run)

    click.echo(
        f"{'[DRY RUN] ' if dry_run else ''}"
        f"Parsed {result.rows_parsed}, "
        f"imported {result.rows_imported}, "
        f"skipped {result.rows_skipped} duplicates"
    )
