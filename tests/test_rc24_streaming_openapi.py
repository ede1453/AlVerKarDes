from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_streaming_api_is_registered_in_openapi():
    response = client.get("/openapi.json")
    assert response.status_code == 200

    paths = response.json()["paths"]

    assert "/api/v1/llm-streaming/preview" in paths
    assert "/api/v1/llm-streaming/sse" in paths
    assert "/api/v1/api/v1/llm-streaming/preview" not in paths
