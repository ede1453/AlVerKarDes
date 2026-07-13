from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_observability_snapshot_get_api_returns_metrics():
    response = client.get("/api/v1/observability/snapshot")

    assert response.status_code == 200

    data = response.json()

    assert "providers" in data
    assert "orchestration" in data
    assert "audit" in data


def test_observability_snapshot_post_api_accepts_provider_scope():
    response = client.post(
        "/api/v1/observability/snapshot",
        json={
            "providers": ["mock"],
            "preferred_provider": "mock",
            "fallback_providers": [],
            "prompt_version": "shopping_v1",
        },
    )

    assert response.status_code == 200
    assert response.json()["status"] == "HEALTHY"
