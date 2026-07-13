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


def test_rc93_vertical_slice_readiness_manifest_promotion():
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

    published = client.post(
        "/api/v1/notification-outbox/release-manifest/publish",
        json={
            "release_version": "v0.6.0",
            "commit_sha": "abc123",
            "build_id": "build-91",
        },
    ).json()

    assert published["published"] is True

    promoted = client.post(
        "/api/v1/notification-outbox/release-promotion/promote",
        json={
            "environment": "staging",
            "promoted_by": "admin",
        },
    ).json()

    assert promoted["promoted"] is True

    status = client.get(
        "/api/v1/notification-outbox/release-promotion/status"
    ).json()

    assert status["status"] == "PROMOTED"
    assert status["promotions"][0]["environment"] == "staging"
