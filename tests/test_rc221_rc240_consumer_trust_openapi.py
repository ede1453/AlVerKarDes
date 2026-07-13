from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

def test_rc221_rc240_routes_registered():
    paths = client.get("/openapi.json").json()["paths"]

    expected = [
        "/api/v1/consumer-trust/clear",
        "/api/v1/consumer-trust/fatigue",
        "/api/v1/consumer-trust/deliveries",
        "/api/v1/consumer-trust/frequency-cap",
        "/api/v1/consumer-trust/provider-health",
        "/api/v1/consumer-trust/provider-fallback",
        "/api/v1/consumer-trust/delivery-sla",
        "/api/v1/consumer-trust/feedback",
        "/api/v1/consumer-trust/acceptance-metrics",
        "/api/v1/consumer-trust/false-positive",
        "/api/v1/consumer-trust/source-trust",
        "/api/v1/consumer-trust/feedback-summary",
        "/api/v1/consumer-trust/budget-policy",
        "/api/v1/consumer-trust/category-quota",
        "/api/v1/consumer-trust/saved-searches",
        "/api/v1/consumer-trust/saved-searches/{user_id}",
        "/api/v1/consumer-trust/compare-deals",
        "/api/v1/consumer-trust/purchase-intents",
        "/api/v1/consumer-trust/conversions",
        "/api/v1/consumer-trust/affiliate-disclosure",
        "/api/v1/consumer-trust/sponsored-compliance",
        "/api/v1/consumer-trust/recommendation-audit",
        "/api/v1/consumer-trust/trust-dashboard",
    ]

    for path in expected:
        assert path in paths
