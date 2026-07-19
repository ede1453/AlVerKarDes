from fastapi.testclient import TestClient

from app.main import app
from tests.auth_test_helpers import operator_headers

client = TestClient(app)


def test_rc103_request_timeline_contains_start_and_completion():
    with TestClient(app) as scoped_client:
        headers = operator_headers(scoped_client)
        scoped_client.post("/api/v1/observability/clear", headers=headers)

        response = scoped_client.get(
            "/health",
            headers={"X-Correlation-ID": "corr-timeline-rc103"},
        )

        assert response.status_code == 200

        timeline = scoped_client.get(
            "/api/v1/observability/timelines/corr-timeline-rc103",
            headers=headers,
        ).json()

    events = timeline["events"]
    event_names = [item["event"] for item in events]

    assert event_names[0] == "REQUEST_STARTED"
    assert "REQUEST_COMPLETED" in event_names
    assert events[-1]["elapsed_ms"] >= 0


def test_rc103_response_contains_duration_header():
    response = client.get("/health")

    duration = float(
        response.headers["X-Response-Time-Ms"]
    )

    assert duration >= 0
