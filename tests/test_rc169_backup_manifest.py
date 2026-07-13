from app.domains.deal_storage.service import DealStorageRepository


def test_rc169_backup_manifest_and_verify():
    repo = DealStorageRepository()
    repo.upsert(
        deal_id="deal-1",
        payload={"status":"VALIDATED"},
        version=1,
    )
    manifest = repo.create_backup_manifest(
        backup_name="daily-backup"
    )
    result = repo.verify_backup_manifest(
        manifest["manifest_id"]
    )
    assert manifest["record_count"] == 1
    assert result["verified"] is True
