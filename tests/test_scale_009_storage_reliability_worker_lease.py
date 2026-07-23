from app.domains.deal_storage.reliability_governance import StorageReliabilityGovernanceService
from app.domains.leader_election.redis_leader_election_store import RedisLeaderElectionStore


class FakeRedis:
    """Same FakeRedis pattern as test_scale_002_redis_leader_election.py --
    reused here to prove StorageReliabilityGovernanceService's worker-lease
    wrapper (not just the underlying store, already covered by SCALE-002's
    own tests) correctly delegates to RedisLeaderElectionStore and produces
    split-brain-free behavior across two service instances sharing one
    Redis connection (simulating two separate worker processes)."""

    def __init__(self):
        self.data = {}
        self.ttls = {}

    def set(self, key, value, nx=False, ex=None):
        if nx and key in self.data:
            return False
        self.data[key] = value
        if ex is not None:
            self.ttls[key] = ex
        return True

    def get(self, key):
        return self.data.get(key)

    def ttl(self, key):
        return self.ttls.get(key, -2)

    def expire(self, key, seconds):
        if key not in self.data:
            return 0
        self.ttls[key] = seconds
        return 1

    def delete(self, *keys):
        removed = 0
        for key in keys:
            if key in self.data:
                del self.data[key]
                removed += 1
            self.ttls.pop(key, None)
        return removed

    def scan_iter(self, match, count=500):
        prefix = match.rstrip("*")
        return [k for k in self.data if k.startswith(prefix)]

    def eval(self, script, numkeys, *args):
        key = args[0]
        if "redis.call('set'" in script:
            worker_id, lease_seconds = args[1], int(args[2])
            current = self.data.get(key)
            if current is None or current == worker_id:
                self.set(key, worker_id, ex=lease_seconds)
                return 1
            return 0
        if "redis.call('expire'" in script:
            worker_id, lease_seconds = args[1], args[2]
            if self.data.get(key) == worker_id:
                return self.expire(key, int(lease_seconds))
            return 0
        worker_id = args[1]
        if self.data.get(key) == worker_id:
            return self.delete(key)
        return 0


def test_scale_009_two_service_instances_share_one_redis_client_no_split_brain():
    # Simulates two separate worker processes: each gets its OWN
    # StorageReliabilityGovernanceService instance (as the router's
    # per-request-agnostic module singleton would across real processes),
    # but both point at the same underlying Redis connection/data -- proving
    # only ONE of them ever holds the worker-lease, unlike the old
    # InMemoryLeaderElectionStore-free `_worker_leases` dict where each
    # process's dict was fully independent (the SCALE-009 defect: two
    # workers could each believe themselves the active storage-reliability
    # worker).
    shared_client = FakeRedis()
    worker_a = StorageReliabilityGovernanceService(leader_store=RedisLeaderElectionStore(shared_client))
    worker_b = StorageReliabilityGovernanceService(leader_store=RedisLeaderElectionStore(shared_client))

    result_a = worker_a.acquire_worker_lease(worker_id="worker-a", lease_seconds=30)
    result_b = worker_b.acquire_worker_lease(worker_id="worker-b", lease_seconds=30)

    assert result_a["acquired"] is True
    assert result_b["acquired"] is False
    assert result_b["reason"] == "LEASE_ALREADY_ACTIVE"
    assert result_b["lease"]["worker_id"] == "worker-a"


def test_scale_009_heartbeat_and_release_then_takeover():
    shared_client = FakeRedis()
    worker_a = StorageReliabilityGovernanceService(leader_store=RedisLeaderElectionStore(shared_client))
    worker_b = StorageReliabilityGovernanceService(leader_store=RedisLeaderElectionStore(shared_client))

    worker_a.acquire_worker_lease(worker_id="worker-a", lease_seconds=30)

    heartbeat = worker_a.heartbeat_worker(worker_id="worker-a", lease_seconds=30)
    assert heartbeat["updated"] is True

    foreign_heartbeat = worker_b.heartbeat_worker(worker_id="worker-b", lease_seconds=30)
    assert foreign_heartbeat["updated"] is False
    assert foreign_heartbeat["reason"] == "LEASE_NOT_FOUND"

    released = worker_a.release_worker_lease(worker_id="worker-a")
    assert released["released"] is True

    takeover = worker_b.acquire_worker_lease(worker_id="worker-b", lease_seconds=30)
    assert takeover["acquired"] is True


def test_scale_009_clear_force_releases_lease_for_next_caller():
    shared_client = FakeRedis()
    worker_a = StorageReliabilityGovernanceService(leader_store=RedisLeaderElectionStore(shared_client))

    worker_a.acquire_worker_lease(worker_id="worker-a", lease_seconds=30)
    worker_a.clear()

    fresh_service = StorageReliabilityGovernanceService(leader_store=RedisLeaderElectionStore(shared_client))
    reacquired = fresh_service.acquire_worker_lease(worker_id="worker-b", lease_seconds=30)

    assert reacquired["acquired"] is True
