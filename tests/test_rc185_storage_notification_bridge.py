from app.domains.deal_storage.operations_runtime import StorageOperationsRuntime


def test_rc185_notification_bridge():
    service = StorageOperationsRuntime()
    result = service.build_storage_notifications(
        dashboard={
            "snapshot_id":"snapshot-1",
            "overall_status":"CRITICAL",
            "score":20,
            "risks":[
                "DATABASE_UNREACHABLE",
                "BACKUP_STALE",
            ],
        },
        recipient_user_ids=[
            "admin-1",
            "admin-2",
        ],
    )
    assert result["should_notify"] is True
    assert result["notification_count"] == 2
    assert result["notifications"][0]["status"] == "PENDING"

def test_rc185_no_notification_when_healthy():
    service = StorageOperationsRuntime()
    result = service.build_storage_notifications(
        dashboard={
            "overall_status":"HEALTHY",
            "score":100,
            "risks":[],
        },
        recipient_user_ids=["admin-1"],
    )
    assert result["should_notify"] is False
    assert result["notification_count"] == 0
