from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_llm_gateway_providers_endpoint_is_registered_in_openapi():
    response = client.get("/openapi.json")
    assert response.status_code == 200

    paths = response.json()["paths"]

    assert "/api/v1/llm-gateway/providers" in paths
    assert "get" in paths["/api/v1/llm-gateway/providers"]
    assert "/api/v1/api/v1/llm-gateway/providers" not in paths
