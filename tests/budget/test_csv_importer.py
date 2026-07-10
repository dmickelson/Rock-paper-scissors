from budget.importers.csv_importer import CsvImporter


def test_parses_all_rows(chase_account, sample_csv):
    importer = CsvImporter(chase_account)
    txns = importer.parse(sample_csv)
    assert len(txns) == 7


def test_amount_sign(chase_account, sample_csv):
    importer = CsvImporter(chase_account)
    txns = importer.parse(sample_csv)
    expenses = [t for t in txns if t.amount < 0]
    income = [t for t in txns if t.amount > 0]
    assert len(expenses) == 6
    assert len(income) == 1


def test_whole_foods_description(chase_account, sample_csv):
    importer = CsvImporter(chase_account)
    txns = importer.parse(sample_csv)
    wf = next(t for t in txns if "WHOLE FOODS" in t.description)
    assert wf.amount == -87.43
    assert wf.account_id == "chase_checking"


def test_normalized_desc_uppercase(chase_account, sample_csv):
    importer = CsvImporter(chase_account)
    txns = importer.parse(sample_csv)
    for t in txns:
        assert t.normalized_desc == t.normalized_desc.upper()


def test_txn_ids_unique(chase_account, sample_csv):
    importer = CsvImporter(chase_account)
    txns = importer.parse(sample_csv)
    ids = [t.txn_id for t in txns]
    assert len(ids) == len(set(ids))


def test_source_is_csv(chase_account, sample_csv):
    importer = CsvImporter(chase_account)
    txns = importer.parse(sample_csv)
    assert all(t.source == "csv" for t in txns)
