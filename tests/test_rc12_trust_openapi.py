from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_trust_intelligence_api_is_registered_in_openapi():
    response = client.get("/openapi.json")
    assert response.status_code == 200

    paths = response.json()["paths"]

    assert "/api/v1/trust-intelligence/signals" in paths
    assert "/api/v1/trust-intelligence/evaluate" in paths
    assert "/api/v1/trust-intelligence/profiles/{entity_type}/{entity_id}" in paths
    assert "/api/v1/api/v1/trust-intelligence/evaluate" not in paths
