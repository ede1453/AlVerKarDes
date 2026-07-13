from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_marketplace_aggregation_api_registered_in_openapi():
    paths = client.get("/openapi.json").json()["paths"]
    assert "/api/v1/marketplace-aggregation/aggregate" in paths
    assert "/api/v1/marketplace-aggregation/aggregate-cached" in paths
    assert "/api/v1/api/v1/marketplace-aggregation/aggregate" not in paths
