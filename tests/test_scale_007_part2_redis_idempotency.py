import pytest

from app.domains.deal_notifications.idempotency_store import InMemoryIdempotencyStore
from app.domains.deal_notifications.operations import DealNotificationOperationsService
from app.domains.deal_notifications.redis_idempotency_store import RedisIdempotencyStore


class FakeRedis:
    """Mirrors tests/test_scale_001_redis_rate_limit.py's FakeRedis pattern,
    extended with the SET NX EX / GET / SCAN / DELETE primitives
    RedisIdempotencyStore needs. Backed by a plain dict shared across
    however many FakeRedis references point at it -- used below to
    simulate two separate worker processes sharing one real Redis instance.
    """

    def __init__(self):
        self.data = {}
        self.ttls = {}

    def set(self, key, value, nx=False, ex=None):
        if nx and key in self.data:
            return None
        self.data[key] = value.encode() if isinstance(value, str) else value
        if ex is not None:
            self.ttls[key] = ex
        return True

    def get(self, key):
        return self.data.get(key)

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


class FakeRedisModule:
    class Redis:
        @staticmethod
        def from_url(url, decode_responses=False):
            return FakeRedis()


def test_scale_007_redis_store_reserve_blocks_duplicate():
    store = RedisIdempotencyStore(FakeRedis())

    first = store.reserve("key-1", "notif-a", ttl_seconds=60)
    second = store.reserve("key-1", "notif-b", ttl_seconds=60)

    assert first is None
    assert second == "notif-a"


def test_scale_007_redis_store_reset_clears_only_idempotency_keys():
    client = FakeRedis()
    store = RedisIdempotencyStore(client)
    store.reserve("key-1", "notif-a", ttl_seconds=60)
    client.data["some:other:namespace:key"] = b"unrelated"

    store.reset()

    assert client.data == {"some:other:namespace:key": b"unrelated"}


def test_scale_007_two_store_instances_share_one_redis_client():
    # Simulates two separate worker processes: each gets its OWN
    # RedisIdempotencyStore instance (as DealNotificationOperationsService()
    # does per-process), but both point at the same underlying Redis
    # connection/data -- proving only ONE of them wins the reservation,
    # unlike InMemoryIdempotencyStore where each process's dict would be
    # fully independent (the SCALE-007 Part 2 defect: two workers could
    # each send their own duplicate notification for the same deal).
    shared_client = FakeRedis()
    worker_a_store = RedisIdempotencyStore(shared_client)
    worker_b_store = RedisIdempotencyStore(shared_client)

    result_a = worker_a_store.reserve("dedup-key", "notif-from-a", ttl_seconds=60)
    result_b = worker_b_store.reserve("dedup-key", "notif-from-b", ttl_seconds=60)

    assert result_a is None
    assert result_b == "notif-from-a"


def test_scale_007_service_reserve_via_redis_backed_store_only_one_wins():
    shared_client = FakeRedis()
    worker_a = DealNotificationOperationsService(idempotency_store=RedisIdempotencyStore(shared_client))
    worker_b = DealNotificationOperationsService(idempotency_store=RedisIdempotencyStore(shared_client))

    result_a = worker_a.reserve_idempotency_key(user_id="u1", deal_id="d1", channel="push", window_key="2026-07-23")
    result_b = worker_b.reserve_idempotency_key(user_id="u1", deal_id="d1", channel="push", window_key="2026-07-23")

    assert result_a["reserved"] is True
    assert result_b["reserved"] is False
    assert result_b["reason"] == "DUPLICATE_NOTIFICATION"
    assert result_b["notification_id"] == result_a["notification_id"]


def test_scale_007_in_memory_store_reserve_blocks_duplicate():
    store = InMemoryIdempotencyStore()

    first = store.reserve("key-1", "notif-a", ttl_seconds=60)
    second = store.reserve("key-1", "notif-b", ttl_seconds=60)

    assert first is None
    assert second == "notif-a"


def test_scale_007_factory_selects_redis_with_fake_module(monkeypatch):
    import sys

    monkeypatch.setenv("AICI_CACHE_BACKEND", "redis")
    monkeypatch.setenv("AICI_REDIS_URL", "redis://example-redis:6379/0")
    monkeypatch.setitem(sys.modules, "redis", FakeRedisModule)

    from app.domains.deal_notifications.idempotency_store_factory import get_idempotency_store

    store = get_idempotency_store()

    assert store.__class__.__name__ == "RedisIdempotencyStore"


def test_scale_007_factory_raises_clear_error_if_redis_package_missing(monkeypatch):
    import sys

    monkeypatch.setenv("AICI_CACHE_BACKEND", "redis")
    monkeypatch.setitem(sys.modules, "redis", None)

    from app.domains.deal_notifications.idempotency_store_factory import get_idempotency_store

    with pytest.raises(RuntimeError, match="redis paketi yüklü değil"):
        get_idempotency_store()


def test_scale_007_factory_defaults_to_memory_store_without_redis_backend(monkeypatch):
    monkeypatch.delenv("AICI_CACHE_BACKEND", raising=False)

    from app.domains.deal_notifications.idempotency_store_factory import get_idempotency_store

    store = get_idempotency_store()

    assert store.__class__.__name__ == "InMemoryIdempotencyStore"
