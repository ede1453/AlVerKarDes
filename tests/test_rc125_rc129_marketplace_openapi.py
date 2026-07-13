from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

def test_marketplace_routes_registered():
    paths = client.get("/openapi.json").json()["paths"]
    assert "/api/v1/marketplace-expansion/normalize" in paths
    assert "/api/v1/marketplace-expansion/normalize-batch" in paths
    assert "/api/v1/marketplace-expansion/score" in paths
