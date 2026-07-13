from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_rc102_incoming_correlation_id_is_preserved():
    response = client.get(
        "/health",
        headers={"X-Correlation-ID": "corr-rc102"},
    )

    assert response.status_code == 200
    assert response.headers["X-Correlation-ID"] == "corr-rc102"


def test_rc102_correlation_id_is_generated_when_missing():
    response = client.get("/health")

    correlation_id = response.headers["X-Correlation-ID"]

    assert correlation_id
    assert len(correlation_id) >= 8


def test_rc102_correlation_id_connects_logs_and_timeline():
    client.post("/api/v1/observability/clear")

    client.get(
        "/health",
        headers={"X-Correlation-ID": "corr-link-rc102"},
    )

    logs = client.get(
        "/api/v1/observability/logs",
        params={"correlation_id": "corr-link-rc102"},
    ).json()

    timeline = client.get(
        "/api/v1/observability/timelines/corr-link-rc102"
    ).json()

    assert logs["log_count"] >= 2
    assert timeline["event_count"] >= 2
