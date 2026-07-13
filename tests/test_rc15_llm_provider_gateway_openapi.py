from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_llm_provider_gateway_api_is_registered_in_openapi():
    response = client.get("/openapi.json")
    assert response.status_code == 200

    paths = response.json()["paths"]

    assert "/api/v1/llm-gateway/generate" in paths
    assert "post" in paths["/api/v1/llm-gateway/generate"]
    assert "/api/v1/api/v1/llm-gateway/generate" not in paths
