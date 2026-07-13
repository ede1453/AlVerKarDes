from app.domains.deal_storage.production_readiness import StorageProductionReadinessService


def test_rc194_write_blocked_during_maintenance():
    service = StorageProductionReadinessService()
    registered = service.register_maintenance_window(
        window_id="mw-1",
        starts_at="2026-07-12T20:00:00+00:00",
        ends_at="2026-07-12T22:00:00+00:00",
        operation_type="DATABASE_MAINTENANCE",
        allow_writes=False,
        approved_by="admin",
    )
    assert registered["registered"] is True

    result = service.evaluate_operation_window(
        at_time="2026-07-12T21:00:00+00:00",
        requires_write=True,
    )
    assert result["allowed"] is False
    assert result["reason"] == "WRITE_BLOCKED_BY_MAINTENANCE"
