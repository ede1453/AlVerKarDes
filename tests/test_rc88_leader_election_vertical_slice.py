from fastapi.testclient import TestClient

from app.main import app
from tests.auth_test_helpers import internal_service_headers

client = TestClient(app)


def test_rc88_vertical_slice_acquire_block_release_reacquire():
    first = client.post(
        "/api/v1/notification-outbox/leader/acquire",
        headers=internal_service_headers(),
        json={
            "worker_id": "worker-v1",
            "lease_seconds": 30,
        },
    ).json()

    assert first["acquired"] is True

    blocked = client.post(
        "/api/v1/notification-outbox/leader/acquire",
        headers=internal_service_headers(),
        json={
            "worker_id": "worker-v2",
            "lease_seconds": 30,
        },
    ).json()

    assert blocked["acquired"] is False
    assert blocked["leader_id"] == "worker-v1"

    released = client.post(
        "/api/v1/notification-outbox/leader/release",
        headers=internal_service_headers(),
        json={
            "worker_id": "worker-v1",
        },
    ).json()

    assert released["released"] is True

    second = client.post(
        "/api/v1/notification-outbox/leader/acquire",
        headers=internal_service_headers(),
        json={
            "worker_id": "worker-v2",
            "lease_seconds": 30,
        },
    ).json()

    assert second["acquired"] is True
    assert second["leader_id"] == "worker-v2"
