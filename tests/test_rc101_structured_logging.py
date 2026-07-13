from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_rc101_request_creates_structured_logs():
    client.post("/api/v1/observability/clear")

    response = client.get(
        "/health",
        headers={
            "X-Correlation-ID": "corr-log-rc101",
            "X-Trace-ID": "trace-log-rc101",
        },
    )

    assert response.status_code == 200

    logs = client.get(
        "/api/v1/observability/logs",
        params={"correlation_id": "corr-log-rc101"},
    ).json()

    events = [item["event"] for item in logs["logs"]]

    assert "REQUEST_STARTED" in events
    assert "REQUEST_COMPLETED" in events


def test_rc101_manual_structured_log_contract():
    response = client.post(
        "/api/v1/observability/logs",
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
