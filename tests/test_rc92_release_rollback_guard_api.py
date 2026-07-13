import pytest
from fastapi.testclient import TestClient

import app.api.v1.notification_outbox_router as outbox_router
from app.domains.notifications.outbox.outbox_service import (
    NotificationOutboxService,
)
from app.main import app

client = TestClient(app)


@pytest.fixture(autouse=True)
def reset_notification_outbox_service():
    outbox_router._service = NotificationOutboxService()
    yield
    outbox_router._service = NotificationOutboxService()


def _prepare_release():
    required_checks = [
        "openapi_contract",
        "schema_contract",
        "database_migrations",
        "runtime_health",
        "security_review",
    ]

    for check_name in required_checks:
        client.post(
            "/api/v1/notification-outbox/readiness/checks",
            json={
                "check_name": check_name,
                "passed": True,
                "details": "passed",
            },
        )

    client.post(
        "/api/v1/notification-outbox/release-manifest/publish",
        json={
            "release_version": "v0.6.0",
            "commit_sha": "abc123",
            "build_id": "build-91",
        },
    )


def test_rc92_rollback_status_api_contract():
    response = client.get(
        "/api/v1/notification-outbox/release-rollback/status"
    )

    assert response.status_code == 200
    assert response.json()["status"] == "IDLE"


def test_rc92_request_and_complete_rollback_api_contract():
    _prepare_release()

    requested = client.post(
        "/api/v1/notification-outbox/release-rollback/request",
        json={
            "requested_by": "admin",
            "reason": "deployment failure",
        },
    )

    assert requested.status_code == 200
    assert requested.json()["rollback_requested"] is True

    completed = client.post(
        "/api/v1/notification-outbox/release-rollback/complete",
        json={
            "completed_by": "operator",
        },
    )

    assert completed.status_code == 200
    assert completed.json()["completed"] is True
