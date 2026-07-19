from fastapi.testclient import TestClient

from app.main import app
from tests.auth_test_helpers import operator_headers

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
    with TestClient(app) as scoped_client:
        headers = operator_headers(scoped_client)
        scoped_client.post("/api/v1/observability/clear", headers=headers)

        scoped_client.get(
            "/health",
            headers={"X-Correlation-ID": "corr-link-rc102"},
        )

        logs = scoped_client.get(
            "/api/v1/observability/logs",
            params={"correlation_id": "corr-link-rc102"},
            headers=headers,
        ).json()

        timeline = scoped_client.get(
            "/api/v1/observability/timelines/corr-link-rc102",
            headers=headers,
        ).json()

    assert logs["log_count"] >= 2
    assert timeline["event_count"] >= 2
