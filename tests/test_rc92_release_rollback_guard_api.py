import pytest
from fastapi.testclient import TestClient

import app.api.v1.notification_outbox_router as outbox_router
from app.domains.notifications.outbox.outbox_service import (
    NotificationOutboxService,
)
from app.main import app
from tests.auth_test_helpers import release_manager_headers

client = TestClient(app)


@pytest.fixture(autouse=True)
def reset_notification_outbox_service():
    outbox_router._service = NotificationOutboxService()
    yield
    outbox_router._service = NotificationOutboxService()


def _prepare_release(scoped_client, headers):
    required_checks = [
        "openapi_contract",
        "schema_contract",
        "database_migrations",
        "runtime_health",
        "security_review",
    ]

    for check_name in required_checks:
        scoped_client.post(
            "/api/v1/notification-outbox/readiness/checks",
            headers=headers,
            json={
                "check_name": check_name,
                "passed": True,
                "details": "passed",
            },
        )

    scoped_client.post(
        "/api/v1/notification-outbox/release-manifest/publish",
        headers=headers,
        json={
            "release_version": "v0.6.0",
            "commit_sha": "abc123",
            "build_id": "build-91",
        },
    )


def test_rc92_rollback_status_api_contract():
    with TestClient(app) as scoped_client:
        headers = release_manager_headers(scoped_client)
        response = scoped_client.get(
            "/api/v1/notification-outbox/release-rollback/status",
            headers=headers,
        )

    assert response.status_code == 200
    assert response.json()["status"] == "IDLE"


def test_rc92_request_and_complete_rollback_api_contract():
    with TestClient(app) as scoped_client:
        headers = release_manager_headers(scoped_client)
        _prepare_release(scoped_client, headers)

        requested = scoped_client.post(
            "/api/v1/notification-outbox/release-rollback/request",
            headers=headers,
            json={
                "requested_by": "admin",
                "reason": "deployment failure",
            },
        )

        assert requested.status_code == 200
        assert requested.json()["rollback_requested"] is True

        completed = scoped_client.post(
            "/api/v1/notification-outbox/release-rollback/complete",
            headers=headers,
            json={
                "completed_by": "operator",
            },
        )

    assert completed.status_code == 200
    assert completed.json()["completed"] is True
