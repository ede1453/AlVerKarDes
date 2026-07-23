from fastapi.testclient import TestClient

from app.main import app
from tests.auth_test_helpers import internal_service_headers, operator_headers

# SCALE-007 Part 1: shared/persistent DB -- circuit-breaker status is a
# GLOBAL threshold over dead_letter_count, which (unlike list/membership
# endpoints) has no per-item way to stay robust against leftover dead
# letters from other tests/runs (no /clear -- would disrupt other parallel
# tests too). The exact "empty outbox -> CLOSED -> allowed" business rule is
# already covered with full isolation by
# test_rc75_notification_circuit_breaker_service.py (fresh in-memory
# repository per test); these API tests verify the HTTP contract (routing,
# auth, response shape) instead of an absolute aggregate value.


def test_rc75_circuit_breaker_status_api_contract():
    with TestClient(app) as client:
        headers = operator_headers(client)

        response = client.get(
            "/api/v1/notification-outbox/circuit-breaker/status", headers=headers
        )

    assert response.status_code == 200
    data = response.json()

    assert data["status"] in ("OPEN", "CLOSED")
    assert isinstance(data["failure_count"], int) and data["failure_count"] >= 0
    assert data["metadata"]["circuit_breaker_version"] == "notification_circuit_breaker_v1"


def test_rc75_circuit_breaker_can_deliver_api_contract():
    with TestClient(app) as client:
        response = client.get(
            "/api/v1/notification-outbox/circuit-breaker/can-deliver",
            headers=internal_service_headers(),
        )

    assert response.status_code == 200
    data = response.json()

    assert isinstance(data["allowed"], bool)
    assert data["status"] in ("OPEN", "CLOSED")
    assert data["allowed"] == (data["status"] == "CLOSED")
