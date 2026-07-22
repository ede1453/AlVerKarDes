from fastapi.testclient import TestClient

from app.main import app
from tests.auth_test_helpers import internal_service_headers


def test_job_queue_api_enqueue_and_get():
    with TestClient(app) as client:
        response = client.post(
            "/api/v1/jobs/enqueue",
            json={
                "job_type": "noop",
                "payload": {"x": 1},
            },
            headers=internal_service_headers(),
        )

        assert response.status_code == 200
        job = response.json()

        get_response = client.get(f"/api/v1/jobs/{job['id']}", headers=internal_service_headers())

    assert get_response.status_code == 200
    assert get_response.json()["id"] == job["id"]


def test_job_queue_api_run_now():
    with TestClient(app) as client:
        response = client.post(
            "/api/v1/jobs/run-now",
            json={
                "job_type": "noop",
                "payload": {"x": 1},
            },
            headers=internal_service_headers(),
        )

    assert response.status_code == 200
    assert response.json()["status"] == "COMPLETED"


def test_job_queue_api_claim_next_then_complete():
    # This suite runs against a real, shared, persistent dev database (no
    # per-test isolation key like a fresh user_id -- claim-next intentionally
    # sees the WHOLE queue, that's the point of it), so other tests may have
    # left older PENDING jobs ahead of ours. Drain claims until we find our
    # own job_id rather than assuming FIFO uniqueness -- this is also a more
    # realistic exercise of claim_next() than a guaranteed-empty queue would be.
    with TestClient(app) as client:
        enqueue_response = client.post(
            "/api/v1/jobs/enqueue",
            json={"job_type": "noop", "payload": {"x": 1}},
            headers=internal_service_headers(),
        )
        job_id = enqueue_response.json()["id"]

        claimed = None
        for _ in range(50):
            claim_response = client.post(
                "/api/v1/jobs/claim-next",
                json={"worker_id": "worker-api-1"},
                headers=internal_service_headers(),
            )
            job = claim_response.json()["job"]
            if job is None:
                break
            if job["id"] == job_id:
                claimed = job
                break
            client.post(
                f"/api/v1/jobs/{job['id']}/complete",
                json={"result": {"drained": True}},
                headers=internal_service_headers(),
            )

        assert claimed is not None, "own job was never claimed -- queue drain exceeded retry budget"
        assert claimed["status"] == "RUNNING"
        assert claimed["locked_by"] == "worker-api-1"

        complete_response = client.post(
            f"/api/v1/jobs/{job_id}/complete",
            json={"result": {"status": "ok"}},
            headers=internal_service_headers(),
        )

    assert complete_response.status_code == 200
    assert complete_response.json()["status"] == "COMPLETED"
