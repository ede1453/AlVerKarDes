from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_root_route_points_to_operational_endpoints():
    response = client.get("/")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert payload["health_url"] == "/health"
    assert payload["docs_url"] == "/docs"
    assert payload["release_health_url"] == "/api/v1/system/release-health"
