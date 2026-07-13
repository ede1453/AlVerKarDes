from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_rc62_cache_status_endpoint_still_available():
    response = client.get("/api/v1/cache/status")

    assert response.status_code == 200
    data = response.json()

    assert data["enabled"] is True
    assert data["backend"] in {"memory", "redis"}


def test_rc62_cache_set_get_endpoint_contract_still_works():
    set_response = client.post(
        "/api/v1/cache/set",
        json={
            "key": "rc62:api:cache",
            "value": {"status": "ok"},
            "ttl_seconds": 60,
        },
    )

    assert set_response.status_code == 200
    assert set_response.json()["key"] == "rc62:api:cache"

    get_response = client.post(
        "/api/v1/cache/get",
        json={"key": "rc62:api:cache"},
    )

    assert get_response.status_code == 200
    data = get_response.json()
    assert data["hit"] is True
    assert data["value"] == {"status": "ok"}
