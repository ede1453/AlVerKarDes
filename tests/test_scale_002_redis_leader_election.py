import pytest

from app.domains.leader_election.redis_leader_election_store import RedisLeaderElectionStore


class FakeRedis:
    """Extends the FakeRedis pattern from test_scale_001_redis_rate_limit.py
    with SET NX/EX and a minimal Lua EVAL emulation -- just enough to run
    RedisLeaderElectionStore's actual compare-and-swap renew/release logic
    against real Python semantics (not a hand-written stand-in for it).
    """

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
        # release script
        worker_id = args[1]
        if self.data.get(key) == worker_id:
            return self.delete(key)
        return 0


def test_scale_002_first_worker_acquires_second_is_blocked():
    client = FakeRedis()
    store_a = RedisLeaderElectionStore(client)
    store_b = RedisLeaderElectionStore(client)

    first = store_a.acquire(key="notification_outbox", worker_id="worker-a", lease_seconds=30)
    second = store_b.acquire(key="notification_outbox", worker_id="worker-b", lease_seconds=30)

    assert first["acquired"] is True
    assert second["acquired"] is False
    assert second["reason"] == "LEADER_ALREADY_ACTIVE"
    assert second["leader_id"] == "worker-a"


def test_scale_002_current_leader_can_idempotently_reacquire_own_lock():
    # Matches InMemoryLeaderElectionStore's contract: acquire() only blocks
    # when a DIFFERENT worker_id holds the lock, not the current owner.
    client = FakeRedis()
    store = RedisLeaderElectionStore(client)
    store.acquire(key="notification_outbox", worker_id="worker-a", lease_seconds=30)

    reacquire = store.acquire(key="notification_outbox", worker_id="worker-a", lease_seconds=60)

    assert reacquire["acquired"] is True
    assert reacquire["leader_id"] == "worker-a"


def test_scale_002_only_current_leader_can_renew():
    client = FakeRedis()
    store = RedisLeaderElectionStore(client)
    store.acquire(key="notification_outbox", worker_id="worker-a", lease_seconds=30)

    own_renew = store.renew(key="notification_outbox", worker_id="worker-a", lease_seconds=60)
    foreign_renew = store.renew(key="notification_outbox", worker_id="worker-b", lease_seconds=60)

    assert own_renew["renewed"] is True
    assert foreign_renew["renewed"] is False
    assert foreign_renew["reason"] == "NOT_CURRENT_LEADER"


def test_scale_002_only_current_leader_can_release_then_other_worker_can_acquire():
    client = FakeRedis()
    store = RedisLeaderElectionStore(client)
    store.acquire(key="notification_outbox", worker_id="worker-a", lease_seconds=30)

    foreign_release = store.release(key="notification_outbox", worker_id="worker-b")
    assert foreign_release["released"] is False

    own_release = store.release(key="notification_outbox", worker_id="worker-a")
    assert own_release["released"] is True

    reacquire = store.acquire(key="notification_outbox", worker_id="worker-b", lease_seconds=30)
    assert reacquire["acquired"] is True


def test_scale_002_lock_expiry_lets_a_new_worker_take_over():
    client = FakeRedis()
    store = RedisLeaderElectionStore(client)
    store.acquire(key="notification_outbox", worker_id="worker-a", lease_seconds=30)

    # Simulate real Redis TTL expiry (abandoned lease, no renew/release) --
    # the whole point of moving to Redis: this can't happen with the
    # in-memory dict, which never expires on its own.
    del client.data["aici:leader:notification_outbox"]

    takeover = store.acquire(key="notification_outbox", worker_id="worker-b", lease_seconds=30)
    assert takeover["acquired"] is True
    assert takeover["leader_id"] == "worker-b"


def test_scale_002_factory_selects_redis_with_fake_module(monkeypatch):
    import sys

    class FakeRedisModule:
        class Redis:
            @staticmethod
            def from_url(url, decode_responses=False):
                return FakeRedis()

    monkeypatch.setenv("AICI_CACHE_BACKEND", "redis")
    monkeypatch.setenv("AICI_REDIS_URL", "redis://example-redis:6379/0")
    monkeypatch.setitem(sys.modules, "redis", FakeRedisModule)

    from app.domains.leader_election.leader_election_store_factory import get_leader_election_store

    store = get_leader_election_store()

    assert store.__class__.__name__ == "RedisLeaderElectionStore"


def test_scale_002_factory_raises_clear_error_if_redis_package_missing(monkeypatch):
    import sys

    monkeypatch.setenv("AICI_CACHE_BACKEND", "redis")
    monkeypatch.setitem(sys.modules, "redis", None)

    from app.domains.leader_election.leader_election_store_factory import get_leader_election_store

    with pytest.raises(RuntimeError, match="redis paketi yüklü değil"):
        get_leader_election_store()


def test_scale_002_factory_defaults_to_memory_store_without_redis_backend(monkeypatch):
    monkeypatch.delenv("AICI_CACHE_BACKEND", raising=False)

    from app.domains.leader_election.leader_election_store_factory import get_leader_election_store

    store = get_leader_election_store()

    assert store.__class__.__name__ == "InMemoryLeaderElectionStore"
