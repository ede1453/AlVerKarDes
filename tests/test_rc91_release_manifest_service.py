from app.domains.notifications.outbox.outbox_service import NotificationOutboxService


def test_rc91_release_manifest_defaults_to_unpublished():
    service = NotificationOutboxService()

    result = service.get_release_manifest()

    assert result["published"] is False
    assert result["release_version"] is None
    assert result["metadata"]["manifest_version"] == "release_manifest_v1"


def test_rc91_publish_release_manifest_when_ready():
    service = NotificationOutboxService()

    for check_name in service.REQUIRED_READINESS_CHECKS:
        service.set_readiness_check(
            check_name=check_name,
            passed=True,
            details="passed",
        )

    result = service.publish_release_manifest(
        release_version="v0.6.0",
        commit_sha="abc123",
        build_id="build-91",
    )

    assert result["published"] is True
    assert result["release_version"] == "v0.6.0"
    assert result["commit_sha"] == "abc123"
    assert result["build_id"] == "build-91"
    assert result["published_at"] is not None


def test_rc91_publish_release_manifest_rejected_when_not_ready():
    service = NotificationOutboxService()

    result = service.publish_release_manifest(
        release_version="v0.6.0",
        commit_sha="abc123",
        build_id="build-91",
    )

    assert result["published"] is False
    assert result["reason"] == "PLATFORM_NOT_READY"


def test_rc91_release_manifest_is_immutable_after_publish():
    service = NotificationOutboxService()

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

    result = service.publish_release_manifest(
        release_version="v0.6.1",
        commit_sha="def456",
        build_id="build-92",
    )

    assert result["published"] is False
    assert result["reason"] == "RELEASE_MANIFEST_ALREADY_PUBLISHED"
