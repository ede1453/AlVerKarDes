from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_discount_intelligence_api_registered_in_openapi():
    paths = client.get("/openapi.json").json()["paths"]

    assert "/api/v1/discount-intelligence/analyze" in paths
    assert "/api/v1/discount-intelligence/analyze-cached" in paths
    assert "/api/v1/api/v1/discount-intelligence/analyze" not in paths
