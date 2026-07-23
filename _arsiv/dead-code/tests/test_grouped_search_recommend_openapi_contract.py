from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def _paths():
    return client.get("/openapi.json").json()["paths"]


def test_grouped_search_recommend_contract():
    schema = _paths()["/api/v1/application/grouped-search-recommend"]

    assert "post" in schema
    assert "requestBody" in schema["post"]
    assert "responses" in schema["post"]
    assert "200" in schema["post"]["responses"]
