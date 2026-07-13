from app.domains.deal_storage.sqlalchemy_models import (
    DealStorageBackupManifest,
    DealStorageIntegrityReport,
    DealStorageOutboxEvent,
    DealStorageRecord,
)


def test_rc170_rc175_table_names():
    assert DealStorageRecord.__tablename__ == "deal_storage_records"
    assert DealStorageOutboxEvent.__tablename__ == "deal_storage_outbox_events"
    assert DealStorageIntegrityReport.__tablename__ == "deal_storage_integrity_reports"
    assert DealStorageBackupManifest.__tablename__ == "deal_storage_backup_manifests"
