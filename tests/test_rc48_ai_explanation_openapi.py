from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_ai_explanation_api_registered_in_openapi():
    paths = client.get("/openapi.json").json()["paths"]

    assert "/api/v1/ai-explanation/explain" in paths
    assert "/api/v1/ai-explanation/explain-cached" in paths
    assert "/api/v1/api/v1/ai-explanation/explain" not in paths
