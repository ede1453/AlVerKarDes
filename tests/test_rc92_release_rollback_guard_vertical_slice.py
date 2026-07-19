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


def test_rc92_vertical_slice_publish_request_complete_rollback():
    with TestClient(app) as client:
        headers = release_manager_headers(client)
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
                headers=headers,
                json={
                    "check_name": check_name,
                    "passed": True,
                    "details": "passed",
                },
            )

        published = client.post(
            "/api/v1/notification-outbox/release-manifest/publish",
            headers=headers,
            json={
                "release_version": "v0.6.0",
                "commit_sha": "abc123",
                "build_id": "build-91",
            },
        ).json()

        assert published["published"] is True

        requested = client.post(
            "/api/v1/notification-outbox/release-rollback/request",
            headers=headers,
            json={
                "requested_by": "admin",
                "reason": "deployment failure",
            },
        ).json()

        assert requested["status"] == "REQUESTED"

        completed = client.post(
            "/api/v1/notification-outbox/release-rollback/complete",
            headers=headers,
            json={
                "completed_by": "operator",
            },
        ).json()

    assert completed["status"] == "COMPLETED"
