"""OFX/QFX transaction importer via ofxtools."""

from __future__ import annotations

import json
from datetime import date
from io import BytesIO
from pathlib import Path
from typing import Optional

from budget.importers.base import AbstractImporter
from budget.models import Account, Transaction
from budget.pipeline.deduplicator import make_txn_id
from budget.pipeline.normalizer import normalize_description

try:
    from ofxtools.parser import OFXTree
    _OFXTOOLS_AVAILABLE = True
except ImportError:
    _OFXTOOLS_AVAILABLE = False


def _ofx_date(dt) -> date:
    """Convert an ofxtools datetime to a plain date."""
    if hasattr(dt, "date"):
        return dt.date()
    return dt


class OfxImporter(AbstractImporter):
    def parse(self, source: Path) -> list[Transaction]:
        if not _OFXTOOLS_AVAILABLE:
            raise ImportError("ofxtools is required for OFX/QFX import: pip install ofxtools")

        parser = OFXTree()
        parser.parse(str(source))
        ofx = parser.convert()

        transactions = []
        statements = []

        # Handle both bank and credit-card statement types
        if hasattr(ofx, "account") and ofx.account is not None:
            if hasattr(ofx, "statements"):
                statements = list(ofx.statements)
        elif hasattr(ofx, "statements"):
            statements = list(ofx.statements)

        # ofxtools wraps everything under ofx.statements (list of STMTRS/CCSTMTRS)
        if not statements and hasattr(ofx, "account"):
            statements = [ofx]

        for stmt in statements:
            banktranlist = getattr(stmt, "transactions", [])
            for stmttrn in banktranlist:
                fitid = str(getattr(stmttrn, "fitid", ""))
                name = str(getattr(stmttrn, "name", "") or "")
                memo = str(getattr(stmttrn, "memo", "") or "")
                description = name or memo
                amount = float(getattr(stmttrn, "trnamt", 0))
                dtposted = getattr(stmttrn, "dtposted", None)
                dtavail = getattr(stmttrn, "dtavail", None)

                txn_date = _ofx_date(dtposted) if dtposted else date.today()
                post_date = _ofx_date(dtavail) if dtavail else None

                txn_id = fitid if fitid else make_txn_id(
                    self.account.account_id, txn_date, amount, description
                )

                transactions.append(Transaction(
                    txn_id=txn_id,
                    import_date=date.today(),
                    txn_date=txn_date,
                    post_date=post_date,
                    account_id=self.account.account_id,
                    description=description,
                    normalized_desc=normalize_description(description),
                    amount=amount,
                    source="ofx",
                    raw_data=json.dumps({
                        "fitid": fitid,
                        "name": name,
                        "memo": memo,
                        "trntype": str(getattr(stmttrn, "trntype", "")),
                    }),
                ))

        return transactions
