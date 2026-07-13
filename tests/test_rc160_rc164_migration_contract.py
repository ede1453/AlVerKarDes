from pathlib import Path


def test_rc160_rc164_migration_contract():
    text = Path(
        "alembic/versions/0013_deal_persistence_recovery.py"
    ).read_text(encoding="utf-8")

    assert 'revision = "0013_deal_persistence_recovery"' in text
    assert 'down_revision = "0012_commerce_ingestion_persistence"' in text
    assert '"deal_persistence_records"' in text
    assert '"deal_snapshots"' in text
    assert '"deal_checkpoints"' in text
    assert '"deal_archives"' in text
    assert '"deal_recovery_events"' in text
