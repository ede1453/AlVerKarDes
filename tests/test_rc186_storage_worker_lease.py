from app.domains.deal_storage.reliability_governance import StorageReliabilityGovernanceService
from app.domains.leader_election.leader_election_store_factory import (
    reset_memory_leader_election_store,
)


def test_rc186_acquire_heartbeat_release():
    reset_memory_leader_election_store()
    service = StorageReliabilityGovernanceService()
    acquired = service.acquire_worker_lease(
        worker_id="worker-1",
        lease_seconds=60,
    )
    assert acquired["acquired"] is True

    # SCALE-009: worker-lease now delegates to RedisLeaderElectionStore
    # (SCALE-002's store, reused as-is). Its acquire() lets the CURRENT
    # holder re-acquire its own lease idempotently (leader_id == worker_id
    # is not a conflict) -- this is a deliberate, already-established
    # contract (see leader_election_store.py's docstring and
    # test_scale_002_current_leader_can_idempotently_reacquire_own_lock),
    # not a regression: the old in-memory version's "second acquire for the
    # same worker_id fails" behavior was simply a different, narrower
    # design that this reuse intentionally replaces.
    reacquired = service.acquire_worker_lease(
        worker_id="worker-1",
        lease_seconds=60,
    )
    assert reacquired["acquired"] is True

    # A DIFFERENT worker_id trying to acquire the same (single, shared)
    # lease while worker-1 holds it is the real conflict this store
    # prevents -- this is the split-brain scenario SCALE-009 closes.
    other_worker_attempt = service.acquire_worker_lease(
        worker_id="worker-2",
        lease_seconds=60,
    )
    assert other_worker_attempt["acquired"] is False
    assert other_worker_attempt["reason"] == "LEASE_ALREADY_ACTIVE"

    heartbeat = service.heartbeat_worker(
        worker_id="worker-1"
    )
    assert heartbeat["updated"] is True

    released = service.release_worker_lease(
        worker_id="worker-1"
    )
    assert released["released"] is True

    # Once released, a different worker can now acquire it.
    other_worker_after_release = service.acquire_worker_lease(
        worker_id="worker-2",
        lease_seconds=60,
    )
    assert other_worker_after_release["acquired"] is True
