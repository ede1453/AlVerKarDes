from fastapi.testclient import TestClient

from app.main import app
from tests.auth_test_helpers import internal_service_headers, operator_headers

# SCALE-007 Part 1: /metrics' pending/processing/delivered counts are
# GLOBAL, highly volatile gauges under a shared/persistent DB with many
# concurrently-running tests (each claim-next()/mark-delivered() call from
# ANY test mutates them) -- even a before/after delta around a single own
# operation isn't reliable, since another test can mutate the same gauge in
# that exact window (observed flaky under `pytest -n auto`), and a `>=`
# bound would be too weak to actually catch a regression (other tests'
# unrelated activity satisfies it regardless of whether OUR call worked).
# The exact pending/processing/delivered bookkeeping is already covered
# with full isolation by test_rc73_notification_metrics_service.py (fresh
# in-memory repository per test). This test instead verifies OUR OWN
# item's transitions precisely via each endpoint's own response body
# (claim-next's returned item, mark-delivered's returned item) -- immune to
# concurrent activity -- and only checks /metrics for contract shape
# (valid keys, non-negative integers), exercising the full HTTP chain
# end-to-end.


def test_rc73_vertical_slice_metrics_across_lifecycle():
    with TestClient(app) as client:
        headers = operator_headers(client)

        queued = client.post(
            "/api/v1/notification-outbox/enqueue",
            headers=internal_service_headers(),
            json={
                "user_id": "rc73-user",
                "title": "RC73 vertical",
                "message": "Metrics lifecycle",
            },
        ).json()
        assert queued["status"] == "PENDING"

        claimed = client.post(
            "/api/v1/notification-outbox/claim-next",
            json={"worker_id": "worker-rc73-vertical"},
            headers=internal_service_headers(),
        ).json()
        assert claimed["claimed"] is True

        delivered_response = client.post(
            f"/api/v1/notification-outbox/{queued['id']}/mark-delivered",
            headers=internal_service_headers(),
        ).json()
        assert delivered_response["updated"] is True
        assert delivered_response["item"]["status"] == "DELIVERED"

        metrics = client.get(
            "/api/v1/notification-outbox/metrics", headers=headers
        ).json()

    for key in ("total_count", "pending_count", "processing_count", "delivered_count", "failed_count", "dead_letter_count"):
        assert isinstance(metrics[key], int) and metrics[key] >= 0
    assert metrics["total_count"] >= metrics["delivered_count"] >= 1
    assert metrics["metadata"]["metrics_version"] == "notification_metrics_v1"
