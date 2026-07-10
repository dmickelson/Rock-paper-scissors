"""budget rules commands."""

import click

from budget.rules.engine import CategoryRulesEngine
from budget.rules.loader import load_rules
from budget.rules.tester import test_description
from budget.sheets.client import SheetsClient


@click.group()
def rules_cmd():
    """Manage and test category rules."""


@rules_cmd.command("test")
@click.argument("description")
def test(description: str) -> None:
    """Test which rule category DESCRIPTION would match."""
    client = SheetsClient()
    rules = load_rules(client)
    engine = CategoryRulesEngine(rules)
    test_description(engine, description)


@rules_cmd.command("list")
def list_rules() -> None:
    """List all active category rules sorted by priority."""
    client = SheetsClient()
    rules = load_rules(client)
    active = [r for r in rules if r.active]
    active.sort(key=lambda r: r.priority)
    click.echo(f"{'PRI':>4}  {'CATEGORY':<20}  {'TYPE':<12}  {'FIELD':<15}  PATTERN")
    click.echo("-" * 80)
    for r in active:
        click.echo(
            f"{r.priority:>4}  {r.category_name:<20}  {r.match_type:<12}  "
            f"{r.field:<15}  {r.pattern}"
        )
