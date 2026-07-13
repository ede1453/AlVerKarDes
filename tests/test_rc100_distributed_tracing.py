from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_rc100_response_contains_trace_id():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.headers["X-Trace-ID"]
    assert response.headers["X-Correlation-ID"]


def test_rc100_incoming_trace_id_is_preserved():
    response = client.get(
        "/health",
        headers={"X-Trace-ID": "trace-rc100"},
    )

    assert response.headers["X-Trace-ID"] == "trace-rc100"


def test_rc100_trace_can_be_read_from_api():
    response = client.get(
        "/health",
        headers={
            "X-Trace-ID": "trace-readable-rc100",
            "X-Correlation-ID": "corr-readable-rc100",
        },
    )

    assert response.status_code == 200

    trace_response = client.get(
        "/api/v1/observability/traces/trace-readable-rc100"
    )

    assert trace_response.status_code == 200
    trace = trace_response.json()["trace"]

    assert trace["trace_id"] == "trace-readable-rc100"
    assert trace["correlation_id"] == "corr-readable-rc100"
    assert trace["status"] == "COMPLETED"
    assert trace["status_code"] == 200
    assert trace["duration_ms"] is not None
