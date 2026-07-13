from scripts.check_alembic_linear_history import check_linear_history


def test_alembic_history_is_linear():
    result = check_linear_history()

    assert result["revision_count"] >= 10
    assert result["head"] == "0014_deal_storage_sqlalchemy"
