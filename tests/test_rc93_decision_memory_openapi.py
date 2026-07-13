from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_decision_memory_api_is_registered_in_openapi():
    response = client.get("/openapi.json")
    assert response.status_code == 200

    paths = response.json()["paths"]

    assert "/api/v1/decision-memory/store" in paths
    assert "/api/v1/decision-memory/{decision_id}" in paths
    assert "/api/v1/decision-memory/{decision_id}/outcome" in paths
    assert "/api/v1/api/v1/decision-memory/store" not in paths
