from app.domains.deal_storage.operations_runtime import StorageOperationsRuntime


def test_rc184_dashboard_healthy():
    service = StorageOperationsRuntime()
    result = service.build_health_dashboard(
        storage_health={
            "status":"HEALTHY",
            "score":100,
        },
        pending_outbox_count=0,
        dead_letter_count=0,
        last_backup_age_hours=12,
        latest_restore_drill_successful=True,
    )
    assert result["dashboard"]["overall_status"] == "HEALTHY"
    assert result["dashboard"]["risks"] == []

def test_rc184_dashboard_detects_risks():
    service = StorageOperationsRuntime()
    result = service.build_health_dashboard(
        storage_health={
            "status":"DEGRADED",
            "score":80,
        },
        pending_outbox_count=150,
        dead_letter_count=2,
        last_backup_age_hours=72,
        latest_restore_drill_successful=False,
    )
    assert result["dashboard"]["overall_status"] in {
        "DEGRADED",
        "UNHEALTHY",
    }
    assert len(result["dashboard"]["risks"]) == 4
