from app.domains.notifications.outbox.outbox_service import NotificationOutboxService


def _publish_ready_release(service: NotificationOutboxService) -> None:
    for check_name in service.REQUIRED_READINESS_CHECKS:
        service.set_readiness_check(
            check_name=check_name,
            passed=True,
            details="passed",
        )

    service.publish_release_manifest(
        release_version="v0.6.0",
        commit_sha="abc123",
        build_id="build-91",
    )


def test_rc92_rollback_status_defaults_to_not_requested():
    service = NotificationOutboxService()

    result = service.get_release_rollback_status()

    assert result["rollback_requested"] is False
    assert result["status"] == "IDLE"
    assert result["metadata"]["rollback_version"] == "release_rollback_v1"


def test_rc92_rollback_requires_published_release():
    service = NotificationOutboxService()

    result = service.request_release_rollback(
        requested_by="admin",
        reason="deployment failure",
    )

    assert result["rollback_requested"] is False
    assert result["reason"] == "NO_PUBLISHED_RELEASE"


def test_rc92_request_release_rollback():
    service = NotificationOutboxService()
    _publish_ready_release(service)

    result = service.request_release_rollback(
        requested_by="admin",
        reason="deployment failure",
    )

    assert result["rollback_requested"] is True
    assert result["status"] == "REQUESTED"
    assert result["requested_by"] == "admin"
    assert result["release_version"] == "v0.6.0"


def test_rc92_complete_release_rollback():
    service = NotificationOutboxService()
    _publish_ready_release(service)
    service.request_release_rollback(
        requested_by="admin",
        reason="deployment failure",
    )

    result = service.complete_release_rollback(
        completed_by="operator",
    )

    assert result["completed"] is True
    assert result["status"] == "COMPLETED"
    assert result["completed_by"] == "operator"
    assert result["completed_at"] is not None


def test_rc92_cannot_complete_without_request():
    service = NotificationOutboxService()

    result = service.complete_release_rollback(
        completed_by="operator",
    )

    assert result["completed"] is False
    assert result["reason"] == "ROLLBACK_NOT_REQUESTED"
