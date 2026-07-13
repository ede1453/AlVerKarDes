from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_rc103_request_timeline_contains_start_and_completion():
    client.post("/api/v1/observability/clear")

    response = client.get(
        "/health",
        headers={"X-Correlation-ID": "corr-timeline-rc103"},
    )

    assert response.status_code == 200

    timeline = client.get(
        "/api/v1/observability/timelines/corr-timeline-rc103"
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
