from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_rc301_rc340_routes_registered():
    paths = client.get("/openapi.json").json()["paths"]

    assert "/api/v1/production-launch/clear" in paths
    assert "/api/v1/production-launch/{operation}" in paths
