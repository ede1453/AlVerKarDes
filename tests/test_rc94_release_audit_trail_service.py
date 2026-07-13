from app.domains.notifications.outbox.outbox_service import NotificationOutboxService


def test_rc94_audit_trail_starts_empty():
    service = NotificationOutboxService()

    result = service.get_release_audit_trail()

    assert result["event_count"] == 0
    assert result["events"] == []
    assert result["metadata"]["audit_version"] == "release_audit_trail_v1"


def test_rc94_record_release_audit_event():
    service = NotificationOutboxService()

    result = service.record_release_audit_event(
        event_type="READINESS_CHECK_UPDATED",
        actor="admin",
        details={"check_name": "openapi_contract"},
    )

    assert result["recorded"] is True
    assert result["event"]["event_type"] == "READINESS_CHECK_UPDATED"
    assert result["event"]["actor"] == "admin"
    assert result["event"]["created_at"] is not None


def test_rc94_audit_trail_filters_by_event_type():
    service = NotificationOutboxService()

    service.record_release_audit_event(
        event_type="RELEASE_PUBLISHED",
        actor="admin",
        details={"release_version": "v0.6.0"},
    )
    service.record_release_audit_event(
        event_type="RELEASE_PROMOTED",
        actor="operator",
        details={"environment": "staging"},
    )

    result = service.get_release_audit_trail(
        event_type="RELEASE_PROMOTED"
    )

    assert result["event_count"] == 1
    assert result["events"][0]["event_type"] == "RELEASE_PROMOTED"


def test_rc94_audit_trail_respects_limit():
    service = NotificationOutboxService()

    for index in range(5):
        service.record_release_audit_event(
            event_type="TEST_EVENT",
            actor="system",
            details={"index": index},
        )

    result = service.get_release_audit_trail(limit=2)

    assert result["event_count"] == 2
    assert len(result["events"]) == 2
