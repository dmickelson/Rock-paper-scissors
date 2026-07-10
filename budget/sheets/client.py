"""gspread wrapper: authentication, spreadsheet access, tab helpers."""

from __future__ import annotations

from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from google.oauth2.credentials import Credentials

from budget.config import settings
from budget.sheets import schema


class SheetsClient:
    def __init__(
        self,
        spreadsheet_id: Optional[str] = None,
        credentials=None,
    ) -> None:
        import gspread  # lazy import keeps tests from pulling in google-auth native extensions
        from budget.auth.google_auth import get_credentials

        self._spreadsheet_id = spreadsheet_id or settings.budget_spreadsheet_id
        if not self._spreadsheet_id:
            raise ValueError("BUDGET_SPREADSHEET_ID must be set in .env")

        if credentials is None:
            credentials = get_credentials(
                settings.google_credentials_file,
                settings.google_token_file,
            )

        gc = gspread.authorize(credentials)
        self._spreadsheet = gc.open_by_key(self._spreadsheet_id)

    def worksheet(self, name: str) -> gspread.Worksheet:
        return self._spreadsheet.worksheet(name)

    def get_all_records(self, sheet_name: str) -> list[dict]:
        ws = self.worksheet(sheet_name)
        return ws.get_all_records(default_blank="", numericise_ignore=["all"])

    def append_rows(self, sheet_name: str, rows: list[list]) -> None:
        if not rows:
            return
        ws = self.worksheet(sheet_name)
        ws.append_rows(rows, value_input_option="USER_ENTERED")

    def update_cell(self, sheet_name: str, row: int, col: int, value) -> None:
        ws = self.worksheet(sheet_name)
        ws.update_cell(row, col, value)

    def find_row(self, sheet_name: str, column: str, value: str) -> Optional[int]:
        """Return 1-based row index of the first row where column == value, or None."""
        records = self.get_all_records(sheet_name)
        for i, record in enumerate(records, start=2):  # row 1 is header
            if str(record.get(column, "")) == str(value):
                return i
        return None

    def get_txn_ids(self) -> set[str]:
        """Return the set of all existing txn_id values for fast dedup."""
        ws = self.worksheet(schema.TRANSACTIONS)
        col_values = ws.col_values(1)  # txn_id is column A
        return set(col_values[1:])  # skip header

    def ensure_headers(self) -> None:
        """Write header rows to all sheets if they are empty."""
        header_map = {
            schema.TRANSACTIONS: schema.TRANSACTION_COLUMNS,
            schema.ACCOUNTS: schema.ACCOUNT_COLUMNS,
            schema.CATEGORY_RULES: schema.CATEGORY_RULE_COLUMNS,
            schema.GMAIL_PATTERNS: schema.GMAIL_PATTERN_COLUMNS,
            schema.RECONCILIATION: schema.RECONCILIATION_COLUMNS,
            schema.IMPORT_LOG: schema.IMPORT_LOG_COLUMNS,
        }
        for sheet_name, columns in header_map.items():
            try:
                ws = self.worksheet(sheet_name)
                if not ws.row_values(1):
                    ws.append_row(columns)
            except gspread.exceptions.WorksheetNotFound:
                pass
