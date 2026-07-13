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


def test_rc94_record_release_audit_event_api_contract():
    response = client.post(
        "/api/v1/notification-outbox/release-audit/events",
        json={
            "event_type": "RELEASE_PUBLISHED",
            "actor": "admin",
            "details": {"release_version": "v0.6.0"},
        },
    )

    assert response.status_code == 200
    data = response.json()

    assert data["recorded"] is True
    assert data["event"]["event_type"] == "RELEASE_PUBLISHED"


def test_rc94_get_release_audit_trail_api_contract():
    client.post(
        "/api/v1/notification-outbox/release-audit/events",
        json={
            "event_type": "RELEASE_PROMOTED",
            "actor": "operator",
            "details": {"environment": "staging"},
        },
    )

    response = client.get(
        "/api/v1/notification-outbox/release-audit/events"
    )

    assert response.status_code == 200
    data = response.json()

    assert data["event_count"] == 1
    assert data["events"][0]["event_type"] == "RELEASE_PROMOTED"
