from fastapi.testclient import TestClient

from app.main import app
from tests.auth_test_helpers import operator_headers

client = TestClient(app)


def test_rc90_production_readiness_status_api_contract():
    with TestClient(app) as client:
        headers = operator_headers(client)
        response = client.get(
            "/api/v1/notification-outbox/readiness/status",
            headers=headers,
        )

    assert response.status_code == 200
    data = response.json()

    assert "status" in data
    assert "checks" in data
    assert data["metadata"]["readiness_version"] == "production_readiness_v1"


def test_rc90_update_readiness_check_api_contract():
    with TestClient(app) as client:
        headers = operator_headers(client)
        response = client.post(
            "/api/v1/notification-outbox/readiness/checks",
            headers=headers,
            json={
                "check_name": "openapi_contract",
                "passed": True,
                "details": "OpenAPI guard passed",
            },
        )

    assert response.status_code == 200
    data = response.json()

    assert data["updated"] is True
    assert data["check"]["check_name"] == "openapi_contract"
