"""Priority-ordered regex category rules engine."""

from __future__ import annotations

from budget.models import CategoryRule, Transaction


class CategoryRulesEngine:
    def __init__(self, rules: list[CategoryRule]) -> None:
        self._rules = sorted(
            [r for r in rules if r.active],
            key=lambda r: r.priority,
        )

    def categorize(self, txn: Transaction) -> str:
        for rule in self._rules:
            if rule.matches(txn):
                return rule.category_name
        return "Uncategorized"

    def explain(self, txn: Transaction) -> list[dict]:
        """Return a trace of which rules matched/did-not-match for debugging."""
        results = []
        for rule in self._rules:
            matched = rule.matches(txn)
            results.append({
                "rule_id": rule.rule_id,
                "priority": rule.priority,
                "category": rule.category_name,
                "pattern": rule.pattern,
                "match_type": rule.match_type,
                "field": rule.field,
                "matched": matched,
            })
            if matched:
                break
        return results
