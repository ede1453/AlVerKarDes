import pytest

from app.domains.rate_limits.rate_limit_engine import RateLimitEngine
from app.domains.rate_limits.rate_limit_models import RateLimitRule
from app.domains.rate_limits.redis_rate_limit_store import RedisRateLimitStore


class FakeRedis:
    """Mirrors tests/test_rc611_cache_repository_factory_redis_selection.py's
    FakeRedisClient pattern, extended with the INCR/EXPIRE/TTL/SCAN primitives
    RedisRateLimitStore needs. Backed by a plain dict shared across however
    many FakeRedis references point at it -- used below to simulate two
    separate worker processes sharing one real Redis instance.
    """

    def __init__(self):
        self.data = {}
        self.ttls = {}

    def incr(self, key):
        self.data[key] = self.data.get(key, 0) + 1
        return self.data[key]

    def expire(self, key, seconds):
        self.ttls[key] = seconds
        return True

    def ttl(self, key):
        return self.ttls.get(key, -2)

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


def test_scale_001_redis_store_increments_and_arms_ttl():
    store = RedisRateLimitStore(FakeRedis())

    first = store.increment(key="user-1", scope="password_reset", window_seconds=900)
    second = store.increment(key="user-1", scope="password_reset", window_seconds=900)

    assert first.count == 1
    assert second.count == 2
    assert store.redis_client.ttl(store._redis_key("user-1", "password_reset")) == 900


def test_scale_001_redis_store_reset_clears_only_ratelimit_keys():
    client = FakeRedis()
    store = RedisRateLimitStore(client)
    store.increment(key="user-1", scope="password_reset", window_seconds=900)
    client.data["some:other:namespace:key"] = "unrelated"

    store.reset()

    assert store.redis_client.data == {"some:other:namespace:key": "unrelated"}


def test_scale_001_two_store_instances_share_one_redis_client():
    # Simulates two separate worker processes: each gets its OWN
    # RedisRateLimitStore instance (as RateLimitEngine() does per-process),
    # but both point at the same underlying Redis connection/data -- proving
    # the counter is shared, unlike InMemoryRateLimitStore where each
    # process's dict would be fully independent.
    shared_client = FakeRedis()
    worker_a_store = RedisRateLimitStore(shared_client)
    worker_b_store = RedisRateLimitStore(shared_client)

    a1 = worker_a_store.increment(key="user-1", scope="password_reset", window_seconds=900)
    b1 = worker_b_store.increment(key="user-1", scope="password_reset", window_seconds=900)
    a2 = worker_a_store.increment(key="user-1", scope="password_reset", window_seconds=900)

    assert [a1.count, b1.count, a2.count] == [1, 2, 3]


def test_scale_001_rate_limit_engine_enforces_limit_across_two_redis_backed_stores():
    shared_client = FakeRedis()
    rules = {"password_reset": RateLimitRule(scope="password_reset", limit=5, window_seconds=900)}

    worker_a = RateLimitEngine(store=RedisRateLimitStore(shared_client), rules=rules)
    worker_b = RateLimitEngine(store=RedisRateLimitStore(shared_client), rules=rules)

    results = []
    for engine in (worker_a, worker_b, worker_a, worker_b, worker_a, worker_b):
        results.append(engine.check(key="user-1", scope="password_reset").allowed)

    assert results == [True, True, True, True, True, False]


def test_scale_001_factory_selects_redis_with_fake_module(monkeypatch):
    import sys

    monkeypatch.setenv("AICI_CACHE_BACKEND", "redis")
    monkeypatch.setenv("AICI_REDIS_URL", "redis://example-redis:6379/0")
    monkeypatch.setitem(sys.modules, "redis", FakeRedisModule)

    from app.domains.rate_limits.rate_limit_store_factory import get_rate_limit_store

    store = get_rate_limit_store()

    assert store.__class__.__name__ == "RedisRateLimitStore"


def test_scale_001_factory_raises_clear_error_if_redis_package_missing(monkeypatch):
    import sys

    monkeypatch.setenv("AICI_CACHE_BACKEND", "redis")
    monkeypatch.setitem(sys.modules, "redis", None)

    from app.domains.rate_limits.rate_limit_store_factory import get_rate_limit_store

    with pytest.raises(RuntimeError, match="redis paketi yüklü değil"):
        get_rate_limit_store()


def test_scale_001_factory_defaults_to_memory_store_without_redis_backend(monkeypatch):
    monkeypatch.delenv("AICI_CACHE_BACKEND", raising=False)

    from app.domains.rate_limits.rate_limit_store_factory import get_rate_limit_store

    store = get_rate_limit_store()

    assert store.__class__.__name__ == "InMemoryRateLimitStore"
