from app.domains.deal_storage.operations_runtime import StorageOperationsRuntime


def test_rc183_successful_restore_drill():
    service = StorageOperationsRuntime()
    result = service.run_restore_drill(
        backup_name="daily",
        expected_record_count=100,
        restored_record_count=100,
        integrity_healthy=True,
        duration_ms=1500,
    )
    assert result["drill"]["successful"] is True
    assert result["drill"]["issues"] == []

def test_rc183_failed_restore_drill():
    service = StorageOperationsRuntime()
    result = service.run_restore_drill(
        backup_name="daily",
        expected_record_count=100,
        restored_record_count=99,
        integrity_healthy=False,
        duration_ms=1500,
    )
    assert result["drill"]["successful"] is False
    assert "RECORD_COUNT_MISMATCH" in result["drill"]["issues"]
