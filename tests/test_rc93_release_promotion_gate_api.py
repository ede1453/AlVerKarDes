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


def _prepare_release() -> None:
    for check_name in [
        "openapi_contract",
        "schema_contract",
        "database_migrations",
        "runtime_health",
        "security_review",
    ]:
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


def test_rc93_release_promotion_status_api_contract():
    response = client.get(
        "/api/v1/notification-outbox/release-promotion/status"
    )

    assert response.status_code == 200
    assert response.json()["status"] == "IDLE"


def test_rc93_promote_release_api_contract():
    _prepare_release()

    response = client.post(
        "/api/v1/notification-outbox/release-promotion/promote",
        json={
            "environment": "staging",
            "promoted_by": "admin",
        },
    )

    assert response.status_code == 200
    data = response.json()

    assert data["promoted"] is True
    assert data["environment"] == "staging"
