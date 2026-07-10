"""Budget CLI entry point."""

import click

from budget.cli.import_cmd import import_cmd
from budget.cli.reconcile_cmd import reconcile_cmd
from budget.cli.rules_cmd import rules_cmd
from budget.cli.report_cmd import report_cmd


@click.group()
def cli():
    """Personal budget tracker backed by Google Sheets."""


cli.add_command(import_cmd, name="import")
cli.add_command(reconcile_cmd, name="reconcile")
cli.add_command(rules_cmd, name="rules")
cli.add_command(report_cmd, name="report")


if __name__ == "__main__":
    cli()
