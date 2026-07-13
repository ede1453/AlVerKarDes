from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_cache_status_api_returns_status():
    response = client.get("/api/v1/cache/status")

    assert response.status_code == 200
    assert response.json()["enabled"] is True
    assert response.json()["backend"] == "memory"


def test_cache_set_and_get_api_roundtrip():
    assert client.post("/api/v1/cache/clear").status_code == 200

    set_response = client.post(
        "/api/v1/cache/set",
        json={"key": "api:test", "value": {"hello": "world"}, "ttl_seconds": 60},
    )
    assert set_response.status_code == 200

    get_response = client.post("/api/v1/cache/get", json={"key": "api:test"})

    assert get_response.status_code == 200
    assert get_response.json()["hit"] is True
    assert get_response.json()["value"] == {"hello": "world"}
