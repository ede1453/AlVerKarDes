from app.domains.deal_storage.production_readiness import StorageProductionReadinessService


def test_rc193_access_audit_query():
    service = StorageProductionReadinessService()
    service.record_access_event(
        actor_id="admin-1",
        action="READ",
        resource_type="backup",
        resource_id="backup-1",
        allowed=True,
        reason="AUTHORIZED",
    )
    service.record_access_event(
        actor_id="user-1",
        action="DELETE",
        resource_type="backup",
        resource_id="backup-1",
        allowed=False,
        reason="FORBIDDEN",
    )

    denied = service.query_access_events(
        allowed=False
    )
    assert denied["event_count"] == 1
    assert denied["events"][0]["action"] == "DELETE"
