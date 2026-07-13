from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_streaming_preview_api_returns_events():
    response = client.post(
        "/api/v1/llm-streaming/preview",
        json={
            "text": "MacBook Air is a buy-now candidate.",
            "chunk_size": 10,
            "metadata": {"provider": "mock"},
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["events"][0]["event"] == "start"
    assert data["events"][-1]["event"] == "done"


def test_streaming_sse_api_returns_event_stream():
    with client.stream(
        "POST",
        "/api/v1/llm-streaming/sse",
        json={
            "text": "hello world",
            "chunk_size": 5,
        },
    ) as response:
        assert response.status_code == 200
        assert response.headers["content-type"].startswith("text/event-stream")
        body = response.read().decode("utf-8")

    assert "event: start" in body
    assert "event: token" in body
    assert "event: done" in body
