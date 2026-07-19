from fastapi.testclient import TestClient

from app.main import app
from tests.auth_test_helpers import operator_headers


def test_rate_limit_api_returns_check_result():
    with TestClient(app) as client:
        headers = operator_headers(client)
        response = client.post(
            "/api/v1/rate-limits/check",
            headers=headers,
            json={
                "key": "test-user",
                "scope": "llm_gateway",
            },
        )

    assert response.status_code == 200

    data = response.json()

    assert data["scope"] == "llm_gateway"
    assert data["key"] == "test-user"
    assert "allowed" in data
