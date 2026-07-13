from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_rc104_record_audit_event():
    client.post("/api/v1/observability/clear")

    response = client.post(
        "/api/v1/observability/audit-events",
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
    client.post("/api/v1/observability/clear")

    client.post(
        "/api/v1/observability/audit-events",
        json={
            "event_type": "CONNECTOR_RUN_STARTED",
            "actor": "system",
            "resource": "connector:one",
            "action": "RUN",
            "outcome": "SUCCESS",
        },
    )
    client.post(
        "/api/v1/observability/audit-events",
        json={
            "event_type": "CONNECTOR_RUN_FAILED",
            "actor": "system",
            "resource": "connector:two",
            "action": "RUN",
            "outcome": "FAILED",
        },
    )

    result = client.get(
        "/api/v1/observability/audit-events",
        params={"event_type": "CONNECTOR_RUN_FAILED"},
    ).json()

    assert result["event_count"] == 1
    assert (
        result["events"][0]["event_type"]
        == "CONNECTOR_RUN_FAILED"
    )
