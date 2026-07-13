from app.domains.notifications.outbox.outbox_service import NotificationOutboxService


def test_rc90_readiness_defaults_to_not_ready_without_checks():
    service = NotificationOutboxService()

    result = service.get_production_readiness()

    assert result["status"] == "NOT_READY"
    assert result["passed_check_count"] == 0
    assert result["failed_check_count"] == 5
    assert result["metadata"]["readiness_version"] == "production_readiness_v1"


def test_rc90_register_readiness_check():
    service = NotificationOutboxService()

    result = service.set_readiness_check(
        check_name="openapi_contract",
        passed=True,
        details="OpenAPI guards passed",
    )

    assert result["updated"] is True
    assert result["check"]["check_name"] == "openapi_contract"
    assert result["check"]["passed"] is True


def test_rc90_all_required_checks_make_platform_ready():
    service = NotificationOutboxService()

    for check_name in service.REQUIRED_READINESS_CHECKS:
        service.set_readiness_check(
            check_name=check_name,
            passed=True,
            details="passed",
        )

    result = service.get_production_readiness()

    assert result["status"] == "READY"
    assert result["passed_check_count"] == 5
    assert result["failed_check_count"] == 0


def test_rc90_failed_check_keeps_platform_not_ready():
    service = NotificationOutboxService()

    for check_name in service.REQUIRED_READINESS_CHECKS:
        service.set_readiness_check(
            check_name=check_name,
            passed=check_name != "security_review",
            details="result",
        )

    result = service.get_production_readiness()

    assert result["status"] == "NOT_READY"
    assert result["failed_check_count"] == 1
    assert "security_review" in result["failed_checks"]


def test_rc90_unknown_check_is_rejected():
    service = NotificationOutboxService()

    result = service.set_readiness_check(
        check_name="unknown_check",
        passed=True,
        details="invalid",
    )

    assert result["updated"] is False
    assert result["reason"] == "UNKNOWN_READINESS_CHECK"
