import pytest
from fastapi.testclient import TestClient

import app.api.v1.notification_outbox_router as outbox_router
from app.domains.notifications.outbox.outbox_service import NotificationOutboxService
from app.main import app
from tests.auth_test_helpers import release_manager_headers

client = TestClient(app)

@pytest.fixture(autouse=True)
def reset_service():
    outbox_router._service = NotificationOutboxService()
    yield
    outbox_router._service = NotificationOutboxService()

def prepare(scoped_client, headers):
    for name in ["openapi_contract","schema_contract","database_migrations","runtime_health","security_review"]:
        scoped_client.post("/api/v1/notification-outbox/readiness/checks", headers=headers, json={"check_name":name,"passed":True,"details":"passed"})
    scoped_client.post("/api/v1/notification-outbox/release-manifest/publish", headers=headers, json={"release_version":"v0.6.0","commit_sha":"abc123","build_id":"build-91"})

def test_rc95_status_api():
    with TestClient(app) as scoped_client:
        headers = release_manager_headers(scoped_client)
        response = scoped_client.get("/api/v1/notification-outbox/release-approval/status", headers=headers)
    assert response.status_code == 200
    assert response.json()["status"] == "PENDING"

def test_rc95_approve_revoke_api():
    with TestClient(app) as scoped_client:
        headers = release_manager_headers(scoped_client)
        prepare(scoped_client, headers)
        approved = scoped_client.post("/api/v1/notification-outbox/release-approval/approve", headers=headers, json={"approved_by":"admin","notes":"ready"})
        assert approved.status_code == 200
        assert approved.json()["approved"] is True
        revoked = scoped_client.post("/api/v1/notification-outbox/release-approval/revoke", headers=headers, json={"revoked_by":"admin","reason":"defect"})
    assert revoked.status_code == 200
    assert revoked.json()["revoked"] is True
