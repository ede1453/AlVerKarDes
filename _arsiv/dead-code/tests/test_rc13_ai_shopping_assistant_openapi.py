from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_ai_shopping_assistant_api_is_registered_in_openapi():
    response = client.get("/openapi.json")
    assert response.status_code == 200

    paths = response.json()["paths"]

    assert "/api/v1/ai-shopping-assistant/advise" in paths
    assert "post" in paths["/api/v1/ai-shopping-assistant/advise"]
    assert "/api/v1/api/v1/ai-shopping-assistant/advise" not in paths
