from app.domains.deal_storage.resilience import DealStorageResilienceService


def test_rc178_create_backup_export():
    service = DealStorageResilienceService()
    result = service.create_backup_export(
        backup_name="daily",
        records=[
            {
                "deal_id":"deal-1",
                "payload_hash":"abc",
            }
        ],
        manifests=[],
    )
    assert result["created"] is True
    assert result["export"]["record_count"] == 1
