from app.domains.notifications.outbox.outbox_service import NotificationOutboxService


def _prepare_published_release(service: NotificationOutboxService) -> None:
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


def test_rc93_promotion_status_defaults_to_not_promoted():
    service = NotificationOutboxService()

    result = service.get_release_promotion_status()

    assert result["promoted"] is False
    assert result["status"] == "IDLE"
    assert result["metadata"]["promotion_version"] == "release_promotion_v1"


def test_rc93_release_cannot_be_promoted_without_manifest():
    service = NotificationOutboxService()

    result = service.promote_release(
        environment="staging",
        promoted_by="admin",
    )

    assert result["promoted"] is False
    assert result["reason"] == "NO_PUBLISHED_RELEASE"


def test_rc93_release_cannot_be_promoted_with_pending_rollback():
    service = NotificationOutboxService()
    _prepare_published_release(service)

    service.request_release_rollback(
        requested_by="admin",
        reason="deployment failure",
    )

    result = service.promote_release(
        environment="production",
        promoted_by="admin",
    )

    assert result["promoted"] is False
    assert result["reason"] == "ROLLBACK_IN_PROGRESS"


def test_rc93_release_can_be_promoted_when_ready():
    service = NotificationOutboxService()
    _prepare_published_release(service)

    result = service.promote_release(
        environment="staging",
        promoted_by="admin",
    )

    assert result["promoted"] is True
    assert result["status"] == "PROMOTED"
    assert result["environment"] == "staging"
    assert result["release_version"] == "v0.6.0"
    assert result["promoted_at"] is not None


def test_rc93_same_environment_cannot_be_promoted_twice():
    service = NotificationOutboxService()
    _prepare_published_release(service)

    service.promote_release(
        environment="staging",
        promoted_by="admin",
    )

    result = service.promote_release(
        environment="staging",
        promoted_by="admin",
    )

    assert result["promoted"] is False
    assert result["reason"] == "ENVIRONMENT_ALREADY_PROMOTED"
