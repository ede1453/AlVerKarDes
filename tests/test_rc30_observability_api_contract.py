from fastapi.testclient import TestClient

from app.main import app
from tests.auth_test_helpers import operator_headers


def test_observability_snapshot_get_api_returns_metrics():
    with TestClient(app) as client:
        headers = operator_headers(client)
        response = client.get("/api/v1/observability/snapshot", headers=headers)

    assert response.status_code == 200

    data = response.json()

    assert "providers" in data
    assert "orchestration" in data
    assert "audit" in data


def test_observability_snapshot_post_api_accepts_provider_scope():
    with TestClient(app) as client:
        headers = operator_headers(client)
        response = client.post(
            "/api/v1/observability/snapshot",
            headers=headers,
            json={
                "providers": ["mock"],
                "preferred_provider": "mock",
                "fallback_providers": [],
                "prompt_version": "shopping_v1",
            },
        )

    assert response.status_code == 200
    assert response.json()["status"] == "HEALTHY"
