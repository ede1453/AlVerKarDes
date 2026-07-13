from app.domains.notifications.outbox.outbox_service import NotificationOutboxService


def prepare(service):
    for name in service.REQUIRED_READINESS_CHECKS:
        service.set_readiness_check(name, True, "passed")
    service.publish_release_manifest("v0.6.0", "abc123", "build-91")

def test_rc95_defaults_pending():
    service = NotificationOutboxService()
    result = service.get_release_approval_status()
    assert result["approved"] is False
    assert result["status"] == "PENDING"

def test_rc95_requires_manifest():
    service = NotificationOutboxService()
    result = service.approve_release("admin", "ready")
    assert result["approved"] is False
    assert result["reason"] == "NO_PUBLISHED_RELEASE"

def test_rc95_can_approve_release():
    service = NotificationOutboxService()
    prepare(service)
    result = service.approve_release("admin", "ready")
    assert result["approved"] is True
    assert result["status"] == "APPROVED"
    assert result["release_version"] == "v0.6.0"

def test_rc95_cannot_approve_twice():
    service = NotificationOutboxService()
    prepare(service)
    service.approve_release("admin", "ready")
    result = service.approve_release("operator", "again")
    assert result["approved"] is False
    assert result["reason"] == "RELEASE_ALREADY_APPROVED"

def test_rc95_can_revoke_approval():
    service = NotificationOutboxService()
    prepare(service)
    service.approve_release("admin", "ready")
    result = service.revoke_release_approval("admin", "defect")
    assert result["revoked"] is True
    assert result["status"] == "REVOKED"
