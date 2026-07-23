import pytest

from app.domains.events.event_bus_service import EventBusService
from app.domains.events.event_models import EventCreate, create_event_record
from app.domains.events.redis_event_repository import RedisEventRepository


class FakeRedis:
    """Mirrors tests/test_scale_001_redis_rate_limit.py's FakeRedis pattern,
    extended with the RPUSH/LRANGE/DELETE/LLEN primitives RedisEventRepository
    needs. Backed by a plain dict of lists shared across however many FakeRedis
    references point at it -- used below to simulate two separate worker
    processes sharing one real Redis instance.
    """

    def __init__(self):
        self.lists: dict[str, list[bytes]] = {}

    def rpush(self, key, value):
        raw = value.encode() if isinstance(value, str) else value
        self.lists.setdefault(key, []).append(raw)
        return len(self.lists[key])

    def lrange(self, key, start, end):
        values = self.lists.get(key, [])
        if end == -1:
            return values[start:]
        return values[start:end + 1]

    def delete(self, *keys):
        removed = 0
        for key in keys:
            if key in self.lists:
                del self.lists[key]
                removed += 1
        return removed

    def llen(self, key):
        return len(self.lists.get(key, []))


class FakeRedisModule:
    class Redis:
        @staticmethod
        def from_url(url, decode_responses=False):
            return FakeRedis()


def _event(event_type, source, payload=None):
    return create_event_record(
        EventCreate(event_type=event_type, source=source, payload=payload or {})
    )


def test_scale_006_redis_repository_publish_and_list_recent():
    repo = RedisEventRepository(FakeRedis())

    repo.publish(_event("cache.hit", "cache"))
    repo.publish(_event("cache.miss", "cache"))

    events = repo.list_recent(limit=10, source="cache")

    assert [e.event_type for e in events] == ["cache.miss", "cache.hit"]
    assert repo.count() == 2


def test_scale_006_redis_repository_filters_by_event_type():
    repo = RedisEventRepository(FakeRedis())
    repo.publish(_event("deal_detection.completed", "deal_detection"))
    repo.publish(_event("notification.delivery_completed", "notifications"))

    events = repo.list_recent(limit=10, event_type="deal_detection.completed")

    assert len(events) == 1
    assert events[0].source == "deal_detection"


def test_scale_006_redis_repository_clear_wipes_only_event_key():
    client = FakeRedis()
    repo = RedisEventRepository(client)
    repo.publish(_event("x", "x"))
    client.lists["some:other:namespace:key"] = [b"unrelated"]

    repo.clear()

    assert repo.count() == 0
    assert client.lists["some:other:namespace:key"] == [b"unrelated"]


def test_scale_006_two_repository_instances_share_one_redis_client():
    # Simulates two separate worker processes: each gets its OWN
    # RedisEventRepository instance (as get_event_repository() does per
    # call in redis mode), but both point at the same underlying Redis
    # connection/data -- proving events published on worker A are visible
    # from worker B, unlike InMemoryEventRepository where each process's
    # list would be fully independent (the SCALE-006 defect).
    shared_client = FakeRedis()
    worker_a = RedisEventRepository(shared_client)
    worker_b = RedisEventRepository(shared_client)

    worker_a.publish(_event("shopping_pipeline.completed", "shopping_pipeline"))
    worker_b.publish(_event("shopping_pipeline.completed", "shopping_pipeline"))
    worker_a.publish(_event("shopping_pipeline.completed", "shopping_pipeline"))

    seen_by_worker_b = worker_b.list_recent(limit=50)

    assert len(seen_by_worker_b) == 3
    assert worker_b.count() == 3


def test_scale_006_event_bus_service_reports_redis_backend():
    service = EventBusService(repository=RedisEventRepository(FakeRedis()))

    assert service.status()["backend"] == "redis"


def test_scale_006_factory_selects_redis_with_fake_module(monkeypatch):
    import sys

    monkeypatch.setenv("AICI_CACHE_BACKEND", "redis")
    monkeypatch.setenv("AICI_REDIS_URL", "redis://example-redis:6379/0")
    monkeypatch.setitem(sys.modules, "redis", FakeRedisModule)

    from app.domains.events.event_repository_factory import get_event_repository

    repo = get_event_repository()

    assert repo.__class__.__name__ == "RedisEventRepository"


def test_scale_006_factory_raises_clear_error_if_redis_package_missing(monkeypatch):
    import sys

    monkeypatch.setenv("AICI_CACHE_BACKEND", "redis")
    monkeypatch.setitem(sys.modules, "redis", None)

    from app.domains.events.event_repository_factory import get_event_repository

    with pytest.raises(RuntimeError, match="redis paketi yüklü değil"):
        get_event_repository()


def test_scale_006_factory_defaults_to_memory_repository_without_redis_backend(monkeypatch):
    monkeypatch.delenv("AICI_CACHE_BACKEND", raising=False)

    from app.domains.events.event_repository_factory import get_event_repository

    repo = get_event_repository()

    assert repo.__class__.__name__ == "InMemoryEventRepository"
