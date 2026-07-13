from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_provider_health_api_is_registered_in_openapi():
    response = client.get("/openapi.json")
    assert response.status_code == 200

    paths = response.json()["paths"]

    assert "/api/v1/llm-provider-health/check" in paths
    assert "/api/v1/llm-provider-health/summary" in paths
    assert "/api/v1/api/v1/llm-provider-health/check" not in paths
