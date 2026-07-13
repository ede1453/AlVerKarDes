from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_provider_selection_api_is_registered_in_openapi():
    response = client.get("/openapi.json")
    assert response.status_code == 200

    paths = response.json()["paths"]

    assert "/api/v1/llm-provider-selection/select" in paths
    assert "/api/v1/api/v1/llm-provider-selection/select" not in paths
    assert "/api/v1/llm-orchestration/run-intelligent" in paths
