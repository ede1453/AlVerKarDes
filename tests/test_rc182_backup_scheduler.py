from app.domains.deal_storage.operations_runtime import StorageOperationsRuntime


def test_rc182_backup_schedule_and_run():
    service = StorageOperationsRuntime()
    registered = service.register_backup_schedule(
        schedule_id="daily-backup",
        backup_name_prefix="aici",
        interval_hours=24,
    )
    assert registered["registered"] is True

    result = service.run_backup_schedule(
        schedule_id="daily-backup",
        record_count=100,
        manifest_hash="abc123",
    )
    assert result["executed"] is True
    assert result["backup"]["record_count"] == 100
    assert result["schedule"]["run_count"] == 1
