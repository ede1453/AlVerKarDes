from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

def test_rc186_rc190_vertical_slice():
    client.post(
        "/api/v1/storage-reliability/clear"
    )

    lease = client.post(
        "/api/v1/storage-reliability/worker-leases",
        json={
            "worker_id":"worker-1",
            "lease_seconds":60
        },
    ).json()
    assert lease["acquired"] is True

    approval = client.post(
        "/api/v1/storage-reliability/restore-approvals",
        json={
            "backup_id":"backup-1",
            "requested_by":"operator",
            "environment":"production",
            "reason":"DR test"
        },
    ).json()["approval"]

    client.post(
        f"/api/v1/storage-reliability/restore-approvals/{approval['approval_id']}/decision",
        json={
            "approved":True,
            "decided_by":"admin",
            "decision_reason":"Approved"
        },
    )

    allowed = client.get(
        f"/api/v1/storage-reliability/restore-approvals/{approval['approval_id']}/can-execute"
    ).json()
    assert allowed["allowed"] is True

    slo = client.post(
        "/api/v1/storage-reliability/slo-samples",
        json={
            "availability_pct":99.95,
            "backup_success_pct":100,
            "restore_success_pct":100,
            "outbox_delivery_pct":99.9
        },
    ).json()
    assert slo["sample"]["healthy"] is True
