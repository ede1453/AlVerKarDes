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


def test_rc94_vertical_slice_record_filter_and_list():
    with TestClient(app) as client:
        headers = release_manager_headers(client)
        client.post(
            "/api/v1/notification-outbox/release-audit/events",
            headers=headers,
            json={
                "event_type": "RELEASE_PUBLISHED",
                "actor": "admin",
                "details": {"release_version": "v0.6.0"},
            },
        )
        client.post(
            "/api/v1/notification-outbox/release-audit/events",
            headers=headers,
            json={
                "event_type": "RELEASE_PROMOTED",
                "actor": "operator",
                "details": {"environment": "staging"},
            },
        )

        result = client.get(
            "/api/v1/notification-outbox/release-audit/events",
            headers=headers,
            params={"event_type": "RELEASE_PROMOTED"},
        ).json()

    assert result["event_count"] == 1
    assert result["events"][0]["actor"] == "operator"
    assert result["events"][0]["details"]["environment"] == "staging"
