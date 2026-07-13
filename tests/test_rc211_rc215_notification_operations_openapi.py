from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

def test_rc211_rc215_routes_registered():
    paths = client.get("/openapi.json").json()["paths"]

    for path in [
        "/api/v1/deal-notification-operations/clear",
        "/api/v1/deal-notification-operations/delivery-attempts",
        "/api/v1/deal-notification-operations/delivery-attempts/{notification_id}",
        "/api/v1/deal-notification-operations/idempotency/reserve",
        "/api/v1/deal-notification-operations/escalations",
        "/api/v1/deal-notification-operations/escalations/{escalation_id}/complete",
        "/api/v1/deal-notification-operations/digests",
        "/api/v1/deal-notification-operations/engagement",
        "/api/v1/deal-notification-operations/engagement/metrics",
    ]:
        assert path in paths
