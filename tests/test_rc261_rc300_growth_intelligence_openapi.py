from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

def test_rc261_rc300_routes_registered():
    paths = client.get("/openapi.json").json()["paths"]
    assert "/api/v1/growth-intelligence/clear" in paths
    assert "/api/v1/growth-intelligence/{operation}" in paths
