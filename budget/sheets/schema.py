"""Google Sheets tab names and column definitions."""

TRANSACTIONS = "Transactions"
ACCOUNTS = "Accounts"
CATEGORIES = "Categories"
CATEGORY_RULES = "CategoryRules"
BUDGET = "Budget"
RECONCILIATION = "Reconciliation"
GMAIL_PATTERNS = "GmailPatterns"
IMPORT_LOG = "ImportLog"

ALL_SHEETS = [
    TRANSACTIONS,
    ACCOUNTS,
    CATEGORIES,
    CATEGORY_RULES,
    BUDGET,
    RECONCILIATION,
    GMAIL_PATTERNS,
    IMPORT_LOG,
]

TRANSACTION_COLUMNS = [
    "txn_id", "import_date", "txn_date", "post_date",
    "account_id", "description", "normalized_desc", "amount",
    "category", "subcategory", "tags", "memo",
    "cleared", "reconcile_date", "statement_id", "source", "raw_data",
]

ACCOUNT_COLUMNS = [
    "account_id", "name", "institution", "type", "currency",
    "opening_balance", "opening_date", "active",
    "gmail_sender_pattern", "csv_date_format", "csv_column_map",
]

CATEGORY_RULE_COLUMNS = [
    "rule_id", "priority", "category_name", "field",
    "pattern", "match_type", "amount_min", "amount_max", "active", "notes",
]

GMAIL_PATTERN_COLUMNS = [
    "pattern_id", "institution", "sender_regex", "subject_regex",
    "amount_regex", "merchant_regex", "date_regex", "account_id", "active",
]

RECONCILIATION_COLUMNS = [
    "statement_id", "account_id", "statement_date",
    "opening_balance", "closing_balance",
    "cleared_balance", "difference", "status", "reconciled_date",
]

IMPORT_LOG_COLUMNS = [
    "import_id", "timestamp", "source", "filename",
    "account_id", "rows_parsed", "rows_imported", "rows_skipped", "errors",
]
