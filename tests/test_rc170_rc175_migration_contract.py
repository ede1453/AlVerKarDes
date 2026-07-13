from pathlib import Path


def test_rc170_rc175_migration_contract():
    text = Path(
        "alembic/versions/0014_deal_storage_sqlalchemy.py"
    ).read_text(encoding="utf-8")

    assert 'revision = "0014_deal_storage_sqlalchemy"' in text
    assert 'down_revision = "0013_deal_persistence_recovery"' in text
    assert '"deal_storage_records"' in text
    assert '"deal_storage_outbox_events"' in text
    assert '"deal_storage_integrity_reports"' in text
    assert '"deal_storage_backup_manifests"' in text
