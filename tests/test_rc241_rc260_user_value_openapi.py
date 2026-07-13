from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

def test_rc241_rc260_routes_registered():
    paths = client.get("/openapi.json").json()["paths"]

    expected = [
        "/api/v1/user-value/clear",
        "/api/v1/user-value/savings/calculate",
        "/api/v1/user-value/savings/events",
        "/api/v1/user-value/savings/{user_id}",
        "/api/v1/user-value/price-trend",
        "/api/v1/user-value/purchase-timing",
        "/api/v1/user-value/target-price",
        "/api/v1/user-value/alternatives",
        "/api/v1/user-value/price-alert",
        "/api/v1/user-value/watch",
        "/api/v1/user-value/watch/expire",
        "/api/v1/user-value/decision/explain",
        "/api/v1/user-value/decision/consistency",
        "/api/v1/user-value/journey/events",
        "/api/v1/user-value/journey/funnel",
        "/api/v1/user-value/recommendation-value",
        "/api/v1/user-value/churn-risk",
        "/api/v1/user-value/retention-action",
        "/api/v1/user-value/purchases",
        "/api/v1/user-value/repeat-purchase",
        "/api/v1/user-value/dashboard",
    ]

    for path in expected:
        assert path in paths
