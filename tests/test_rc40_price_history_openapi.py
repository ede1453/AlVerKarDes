from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_price_history_api_registered_in_openapi():
    paths = client.get("/openapi.json").json()["paths"]

    assert "/api/v1/price-history/points" in paths
    assert "/api/v1/price-history/points/bulk" in paths
    assert "/api/v1/price-history/{product_key}/summary" in paths
    assert "/api/v1/api/v1/price-history/points" not in paths
