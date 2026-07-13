from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

def test_rc216_rc220_routes_registered():
    paths = client.get("/openapi.json").json()["paths"]

    for path in [
        "/api/v1/deal-notification-providers/clear",
        "/api/v1/deal-notification-providers/providers",
        "/api/v1/deal-notification-providers/providers/select",
        "/api/v1/deal-notification-providers/delivery-policy/evaluate",
        "/api/v1/deal-notification-providers/subscriptions",
        "/api/v1/deal-notification-providers/subscriptions/unsubscribed",
        "/api/v1/deal-notification-providers/experiments",
        "/api/v1/deal-notification-providers/experiments/{experiment_id}/assign",
        "/api/v1/deal-notification-providers/performance",
    ]:
        assert path in paths
