from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_marketplace_connector_api_registered_in_openapi():
    paths = client.get("/openapi.json").json()["paths"]

    assert "/api/v1/marketplace-connectors" in paths
    assert "/api/v1/marketplace-connectors/search" in paths
    assert "/api/v1/api/v1/marketplace-connectors/search" not in paths
