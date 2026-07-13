from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_rc72_dlq_replay_endpoint_still_registered():
    paths = client.get("/openapi.json").json()["paths"]

    path = "/api/v1/notification-outbox/dead-letters/{item_id}/replay"

    assert path in paths
    assert "post" in paths[path]
    assert "requestBody" in paths[path]["post"]
