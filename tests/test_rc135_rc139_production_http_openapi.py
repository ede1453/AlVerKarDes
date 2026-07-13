from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

def test_rc135_rc139_routes_registered():
    paths = client.get(
        "/openapi.json"
    ).json()["paths"]

    assert "/api/v1/production-http/clear" in paths
    assert "/api/v1/production-http/fixture-pages" in paths
    assert "/api/v1/production-http/execute" in paths
