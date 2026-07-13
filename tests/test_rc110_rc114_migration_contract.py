from pathlib import Path


def test_rc110_rc114_migration_contract():
    text = Path("alembic/versions/0012_commerce_ingestion_persistence.py").read_text(encoding="utf-8")
    assert 'revision = "0012_commerce_ingestion_persistence"' in text
    assert 'down_revision = "0011_notification_outbox"' in text
    assert '"commerce_sources"' in text
    assert '"commerce_import_jobs"' in text
    assert '"commerce_quarantine_items"' in text
