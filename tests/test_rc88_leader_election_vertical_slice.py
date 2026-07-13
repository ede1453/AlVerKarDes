from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_rc88_vertical_slice_acquire_block_release_reacquire():
    first = client.post(
        "/api/v1/notification-outbox/leader/acquire",
        json={
            "worker_id": "worker-v1",
            "lease_seconds": 30,
        },
    ).json()

    assert first["acquired"] is True

    blocked = client.post(
        "/api/v1/notification-outbox/leader/acquire",
        json={
            "worker_id": "worker-v2",
            "lease_seconds": 30,
        },
    ).json()

    assert blocked["acquired"] is False
    assert blocked["leader_id"] == "worker-v1"

    released = client.post(
        "/api/v1/notification-outbox/leader/release",
        json={
            "worker_id": "worker-v1",
        },
    ).json()

    assert released["released"] is True

    second = client.post(
        "/api/v1/notification-outbox/leader/acquire",
        json={
            "worker_id": "worker-v2",
            "lease_seconds": 30,
        },
    ).json()

    assert second["acquired"] is True
    assert second["leader_id"] == "worker-v2"
