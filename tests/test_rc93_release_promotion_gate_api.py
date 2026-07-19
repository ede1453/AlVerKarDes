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


def _prepare_release(scoped_client, headers) -> None:
    for check_name in [
        "openapi_contract",
        "schema_contract",
        "database_migrations",
        "runtime_health",
        "security_review",
    ]:
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


def test_rc93_release_promotion_status_api_contract():
    with TestClient(app) as scoped_client:
        headers = release_manager_headers(scoped_client)
        response = scoped_client.get(
            "/api/v1/notification-outbox/release-promotion/status",
            headers=headers,
        )

    assert response.status_code == 200
    assert response.json()["status"] == "IDLE"


def test_rc93_promote_release_api_contract():
    with TestClient(app) as scoped_client:
        headers = release_manager_headers(scoped_client)
        _prepare_release(scoped_client, headers)

        response = scoped_client.post(
            "/api/v1/notification-outbox/release-promotion/promote",
            headers=headers,
            json={
                "environment": "staging",
                "promoted_by": "admin",
            },
        )

    assert response.status_code == 200
    data = response.json()

    assert data["promoted"] is True
    assert data["environment"] == "staging"
