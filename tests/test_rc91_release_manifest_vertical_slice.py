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


def test_rc91_vertical_slice_readiness_to_release_manifest():
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

    published = client.post(
        "/api/v1/notification-outbox/release-manifest/publish",
        json={
            "release_version": "v0.6.0",
            "commit_sha": "abc123",
            "build_id": "build-91",
        },
    ).json()

    assert published["published"] is True

    status = client.get(
        "/api/v1/notification-outbox/release-manifest"
    ).json()

    assert status["published"] is True
    assert status["release_version"] == "v0.6.0"
    assert status["commit_sha"] == "abc123"
