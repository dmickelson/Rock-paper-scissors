from budget.pipeline.normalizer import normalize_amount, normalize_description


def test_uppercase():
    assert normalize_description("whole foods market") == "WHOLE FOODS MARKET"


def test_strips_purchase_noise():
    result = normalize_description("PURCHASE WHOLE FOODS MARKET #1234")
    assert "PURCHASE" not in result
    assert "#1234" not in result


def test_strips_pos():
    result = normalize_description("POS STARBUCKS 12/01")
    assert "POS" not in result


def test_collapses_spaces():
    result = normalize_description("WHOLE  FOODS   MARKET")
    assert "  " not in result


def test_normalize_amount_debit():
    assert normalize_amount(50.0, "debit") == -50.0


def test_normalize_amount_credit():
    assert normalize_amount(50.0, "credit") == 50.0


def test_normalize_amount_already_negative():
    assert normalize_amount(-50.0, "debit") == -50.0
