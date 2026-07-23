from fastapi.testclient import TestClient

from app.main import app
from tests.auth_test_helpers import internal_service_headers


def test_provider_scheduler_api_create_get_run_once():
    with TestClient(app) as client:
        response = client.post(
            "/api/v1/provider-schedules",
            json={
                "name": "provider-health",
                "providers": ["mock"],
                "interval_seconds": 30,
            },
            headers=internal_service_headers(),
        )

        assert response.status_code == 200
        schedule = response.json()

        get_response = client.get(
            f"/api/v1/provider-schedules/{schedule['id']}", headers=internal_service_headers()
        )
        assert get_response.status_code == 200

        run_response = client.post(
            f"/api/v1/provider-schedules/{schedule['id']}/run-once",
            headers=internal_service_headers(),
        )

    assert run_response.status_code == 200
    assert run_response.json()["result"]["status"] == "HEALTHY"


def test_provider_scheduler_api_list():
    with TestClient(app) as client:
        response = client.get("/api/v1/provider-schedules", headers=internal_service_headers())

    assert response.status_code == 200
    assert "items" in response.json()


def test_provider_scheduler_api_claim_next_then_complete():
    # SCALE-004: claim-next(schedule_id=<ours>) locks one specific schedule
    # atomically (guard used internally by run-once too) -- complete()
    # releases the lock and records the result, same shape run-once returns.
    with TestClient(app) as client:
        create_response = client.post(
            "/api/v1/provider-schedules",
            json={"name": "claim-target", "providers": ["mock"], "interval_seconds": 30},
            headers=internal_service_headers(),
        )
        schedule_id = create_response.json()["id"]

        claim_response = client.post(
            "/api/v1/provider-schedules/claim-next",
            json={"worker_id": "worker-api-1", "schedule_id": schedule_id},
            headers=internal_service_headers(),
        )
        claimed = claim_response.json()["schedule"]
        assert claimed["id"] == schedule_id
        assert claimed["status"] == "RUNNING"
        assert claimed["locked_by"] == "worker-api-1"

        complete_response = client.post(
            f"/api/v1/provider-schedules/{schedule_id}/complete",
            json={"result": {"status": "HEALTHY"}},
            headers=internal_service_headers(),
        )

    assert complete_response.status_code == 200
    body = complete_response.json()
    assert body["schedule"]["status"] == "ACTIVE"
    assert body["schedule"]["locked_by"] is None
    assert body["result"] == {"status": "HEALTHY"}
    assert body["event"]["event_type"] == "provider_health.checked"


def test_provider_scheduler_api_run_once_skips_when_already_claimed():
    # Negative-shape guard: a concurrent claim already holds the lock, so a
    # second run-once on the same schedule must not execute a second health
    # check -- it should observe ALREADY_RUNNING instead.
    with TestClient(app) as client:
        create_response = client.post(
            "/api/v1/provider-schedules",
            json={"name": "already-running", "providers": ["mock"], "interval_seconds": 30},
            headers=internal_service_headers(),
        )
        schedule_id = create_response.json()["id"]

        client.post(
            "/api/v1/provider-schedules/claim-next",
            json={"worker_id": "other-worker", "schedule_id": schedule_id},
            headers=internal_service_headers(),
        )

        run_response = client.post(
            f"/api/v1/provider-schedules/{schedule_id}/run-once",
            headers=internal_service_headers(),
        )

    assert run_response.status_code == 200
    body = run_response.json()
    assert body["result"] == {"status": "SKIPPED", "reason": "ALREADY_RUNNING"}
    assert body["event"] is None
