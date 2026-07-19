from pathlib import Path

def test_rc441_rc450_migration_contract():
    text = Path(
        "alembic/versions/0015_authentication_core.py"
    ).read_text(encoding="utf-8")
    assert 'revision = "0015_authentication_core"' in text
    assert 'down_revision = "0014_deal_storage_sqlalchemy"' in text
    for table in (
        "auth_sessions",
        "auth_tokens",
        "auth_login_attempts",
        "auth_account_security",
        "auth_password_history",
        "auth_audit_events",
    ):
        assert table in text
