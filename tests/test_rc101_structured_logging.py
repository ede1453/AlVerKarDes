from fastapi.testclient import TestClient

from app.main import app
from tests.auth_test_helpers import operator_headers

client = TestClient(app)


def test_rc101_request_creates_structured_logs():
    with TestClient(app) as scoped_client:
        headers = operator_headers(scoped_client)
        scoped_client.post("/api/v1/observability/clear", headers=headers)

        response = scoped_client.get(
            "/health",
            headers={
                "X-Correlation-ID": "corr-log-rc101",
                "X-Trace-ID": "trace-log-rc101",
            },
        )

        assert response.status_code == 200

        logs = scoped_client.get(
            "/api/v1/observability/logs",
            params={"correlation_id": "corr-log-rc101"},
            headers=headers,
        ).json()

    events = [item["event"] for item in logs["logs"]]

    assert "REQUEST_STARTED" in events
    assert "REQUEST_COMPLETED" in events


def test_rc101_manual_structured_log_contract():
    with TestClient(app) as scoped_client:
        headers = operator_headers(scoped_client)
        response = scoped_client.post(
            "/api/v1/observability/logs",
            headers=headers,
            json={
                "level": "WARNING",
                "event": "PRICE_SOURCE_DELAYED",
                "message": "Price source response is delayed",
                "correlation_id": "corr-manual-rc101",
                "trace_id": "trace-manual-rc101",
                "context": {
                    "connector": "example-store",
                    "delay_ms": 2500,
                },
            },
        )

    assert response.status_code == 200
    data = response.json()

    assert data["recorded"] is True
    assert data["log"]["level"] == "WARNING"
    assert data["log"]["context"]["delay_ms"] == 2500
