import pytest
from fastapi.testclient import TestClient

import app.api.v1.notification_outbox_router as outbox_router
from app.domains.notifications.outbox.outbox_service import (
    NotificationOutboxService,
)
from app.main import app


@pytest.fixture(autouse=True)
def reset_notification_outbox_service():
    outbox_router._service = NotificationOutboxService()
    yield
    outbox_router._service = NotificationOutboxService()

client = TestClient(app)


def test_rc91_release_manifest_status_api_contract():
    response = client.get(
        "/api/v1/notification-outbox/release-manifest"
    )

    assert response.status_code == 200
    data = response.json()

    assert "published" in data
    assert "metadata" in data


def test_rc91_publish_release_manifest_api_contract():
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

    response = client.post(
        "/api/v1/notification-outbox/release-manifest/publish",
        json={
            "release_version": "v0.6.0",
            "commit_sha": "abc123",
            "build_id": "build-91",
        },
    )

    assert response.status_code == 200
    data = response.json()

    assert data["published"] is True
    assert data["release_version"] == "v0.6.0"
