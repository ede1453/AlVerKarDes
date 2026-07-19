from fastapi.testclient import TestClient

from app.main import app
from tests.auth_test_helpers import operator_headers

client = TestClient(app)


def test_rc104_record_audit_event():
    with TestClient(app) as scoped_client:
        headers = operator_headers(scoped_client)
        scoped_client.post("/api/v1/observability/clear", headers=headers)

        response = scoped_client.post(
            "/api/v1/observability/audit-events",
            headers=headers,
            json={
                "event_type": "CONNECTOR_CONFIGURATION_CHANGED",
                "actor": "admin-user",
                "resource": "connector:example-store",
                "action": "UPDATE",
                "outcome": "SUCCESS",
                "correlation_id": "corr-audit-rc104",
                "details": {
                    "enabled": True,
                    "country": "DE",
                },
            },
        )

    assert response.status_code == 200
    data = response.json()

    assert data["recorded"] is True
    assert data["event"]["actor"] == "admin-user"
    assert data["event"]["outcome"] == "SUCCESS"


def test_rc104_filter_audit_event_stream():
    with TestClient(app) as scoped_client:
        headers = operator_headers(scoped_client)
        scoped_client.post("/api/v1/observability/clear", headers=headers)

        scoped_client.post(
            "/api/v1/observability/audit-events",
            headers=headers,
            json={
                "event_type": "CONNECTOR_RUN_STARTED",
                "actor": "system",
                "resource": "connector:one",
                "action": "RUN",
                "outcome": "SUCCESS",
            },
        )
        scoped_client.post(
            "/api/v1/observability/audit-events",
            headers=headers,
            json={
                "event_type": "CONNECTOR_RUN_FAILED",
                "actor": "system",
                "resource": "connector:two",
                "action": "RUN",
                "outcome": "FAILED",
            },
        )

        result = scoped_client.get(
            "/api/v1/observability/audit-events",
            params={"event_type": "CONNECTOR_RUN_FAILED"},
            headers=headers,
        ).json()

    assert result["event_count"] == 1
    assert (
        result["events"][0]["event_type"]
        == "CONNECTOR_RUN_FAILED"
    )
