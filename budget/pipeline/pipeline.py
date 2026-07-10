"""Orchestrates: parse → normalize → dedup → categorize → write."""

from __future__ import annotations

import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional

from budget.models import Account, Transaction
from budget.pipeline.deduplicator import Deduplicator
from budget.pipeline.normalizer import normalize_description
from budget.rules.engine import CategoryRulesEngine
from budget.sheets import schema
from budget.sheets.client import SheetsClient


class ImportResult:
    def __init__(self) -> None:
        self.rows_parsed = 0
        self.rows_imported = 0
        self.rows_skipped = 0
        self.errors: list[str] = []

    def __repr__(self) -> str:
        return (
            f"ImportResult(parsed={self.rows_parsed}, "
            f"imported={self.rows_imported}, "
            f"skipped={self.rows_skipped}, "
            f"errors={len(self.errors)})"
        )


class ImportPipeline:
    def __init__(
        self,
        client: SheetsClient,
        engine: CategoryRulesEngine,
    ) -> None:
        self._client = client
        self._engine = engine

    def _load_deduplicator(self, existing_raw: Optional[list[str]] = None) -> Deduplicator:
        existing_ids = self._client.get_txn_ids()
        return Deduplicator(existing_ids, existing_raw)

    def run(
        self,
        transactions: list[Transaction],
        source_label: str,
        account_id: str,
        dry_run: bool = False,
    ) -> ImportResult:
        result = ImportResult()
        result.rows_parsed = len(transactions)

        dedup = self._load_deduplicator()
        new_rows: list[list] = []

        for txn in transactions:
            if dedup.is_duplicate(txn.txn_id, txn.raw_data):
                result.rows_skipped += 1
                continue

            # Ensure normalized_desc is set
            if not txn.normalized_desc:
                txn.normalized_desc = normalize_description(txn.description)

            # Categorize
            txn.category = self._engine.categorize(txn)

            dedup.register(txn.txn_id, txn.raw_data)
            new_rows.append(txn.to_row())
            result.rows_imported += 1

        if not dry_run and new_rows:
            self._client.append_rows(schema.TRANSACTIONS, new_rows)
            self._write_import_log(source_label, account_id, result)

        return result

    def _write_import_log(
        self, source_label: str, account_id: str, result: ImportResult
    ) -> None:
        log_row = [
            str(uuid.uuid4()),
            datetime.utcnow().isoformat(),
            source_label.split(":")[0],  # e.g. "csv" from "csv:chase.csv"
            source_label,
            account_id,
            result.rows_parsed,
            result.rows_imported,
            result.rows_skipped,
            json.dumps(result.errors),
        ]
        self._client.append_rows(schema.IMPORT_LOG, [log_row])
