from app.domains.deal_storage.resilience import DealStorageResilienceService


def test_rc179_restore_validation():
    service = DealStorageResilienceService()
    export = service.create_backup_export(
        backup_name="daily",
        records=[
            {
                "deal_id":"deal-1",
                "payload_hash":"abc",
            }
        ],
    )["export"]

    result = service.validate_restore(
        export_id=export["export_id"],
        expected_record_count=1,
    )
    assert result["valid"] is True
    assert result["issues"] == []

def test_rc179_duplicate_deal_detected():
    service = DealStorageResilienceService()
    export = service.create_backup_export(
        backup_name="daily",
        records=[
            {"deal_id":"deal-1","payload_hash":"a"},
            {"deal_id":"deal-1","payload_hash":"b"},
        ],
    )["export"]

    result = service.validate_restore(
        export_id=export["export_id"]
    )
    assert result["valid"] is False
    assert "DUPLICATE_DEAL_ID" in result["issues"]
