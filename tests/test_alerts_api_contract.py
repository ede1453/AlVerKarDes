from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_alerts_routes_exist_in_openapi():
    response = client.get("/openapi.json")
    assert response.status_code == 200

    paths = response.json()["paths"]

    assert "/api/v1/alerts/rules" in paths
    assert "post" in paths["/api/v1/alerts/rules"]

    assert "/api/v1/alerts/rules/offer/{offer_id}" in paths
    assert "get" in paths["/api/v1/alerts/rules/offer/{offer_id}"]

    assert "/api/v1/alerts/rules/{rule_id}" in paths
    assert "delete" in paths["/api/v1/alerts/rules/{rule_id}"]
