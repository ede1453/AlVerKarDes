import pytest
from fastapi.testclient import TestClient

import app.api.v1.notification_outbox_router as outbox_router
from app.domains.notifications.outbox.outbox_service import NotificationOutboxService
from app.main import app

client = TestClient(app)

@pytest.fixture(autouse=True)
def reset_service():
    outbox_router._service = NotificationOutboxService()
    yield
    outbox_router._service = NotificationOutboxService()

def test_rc95_vertical_slice():
    for name in ["openapi_contract","schema_contract","database_migrations","runtime_health","security_review"]:
        client.post("/api/v1/notification-outbox/readiness/checks", json={"check_name":name,"passed":True,"details":"passed"})
    client.post("/api/v1/notification-outbox/release-manifest/publish", json={"release_version":"v0.6.0","commit_sha":"abc123","build_id":"build-91"})
    approved = client.post("/api/v1/notification-outbox/release-approval/approve", json={"approved_by":"admin","notes":"ready"}).json()
    assert approved["status"] == "APPROVED"
    revoked = client.post("/api/v1/notification-outbox/release-approval/revoke", json={"revoked_by":"admin","reason":"defect"}).json()
    assert revoked["status"] == "REVOKED"
