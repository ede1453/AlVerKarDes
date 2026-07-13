from app.domains.deal_storage.reliability_governance import StorageReliabilityGovernanceService


def test_rc186_acquire_heartbeat_release():
    service = StorageReliabilityGovernanceService()
    acquired = service.acquire_worker_lease(
        worker_id="worker-1",
        lease_seconds=60,
    )
    assert acquired["acquired"] is True

    duplicate = service.acquire_worker_lease(
        worker_id="worker-1",
        lease_seconds=60,
    )
    assert duplicate["acquired"] is False
    assert duplicate["reason"] == "LEASE_ALREADY_ACTIVE"

    heartbeat = service.heartbeat_worker(
        worker_id="worker-1"
    )
    assert heartbeat["updated"] is True

    released = service.release_worker_lease(
        worker_id="worker-1"
    )
    assert released["released"] is True
