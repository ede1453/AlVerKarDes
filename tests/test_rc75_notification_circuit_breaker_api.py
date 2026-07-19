from fastapi.testclient import TestClient

from app.main import app
from tests.auth_test_helpers import internal_service_headers, operator_headers


def test_rc75_circuit_breaker_status_api_contract():
    with TestClient(app) as client:
        headers = operator_headers(client)
        client.post("/api/v1/notification-outbox/clear", headers=headers)

        response = client.get(
            "/api/v1/notification-outbox/circuit-breaker/status", headers=headers
        )

    assert response.status_code == 200
    data = response.json()

    assert data["status"] == "CLOSED"
    assert data["failure_count"] == 0
    assert data["metadata"]["circuit_breaker_version"] == "notification_circuit_breaker_v1"


def test_rc75_circuit_breaker_can_deliver_api_contract():
    with TestClient(app) as client:
        headers = operator_headers(client)
        client.post("/api/v1/notification-outbox/clear", headers=headers)

        response = client.get(
            "/api/v1/notification-outbox/circuit-breaker/can-deliver",
            headers=internal_service_headers(),
        )

    assert response.status_code == 200
    data = response.json()

    assert data["allowed"] is True
    assert data["status"] == "CLOSED"
