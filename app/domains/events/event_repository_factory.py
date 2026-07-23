import os

from app.domains.events.event_repository import InMemoryEventRepository

# SCALE-006: mirrors app/domains/rate_limits/rate_limit_store_factory.py
# (SCALE-001) exactly -- same env var (AICI_CACHE_BACKEND), same reasoning.
# Since AICI_CACHE_BACKEND=redis is already set in .env.prod (SCALE-001/002
# put it there), the event log becomes Redis-backed automatically, no new
# configuration. The in-memory singleton below stays the default/test path
# (AICI_CACHE_BACKEND unset in the pytest suite -- see tests/conftest.py) --
# test_rc351_event_repository_singleton.py depends on get_event_repository()
# returning the SAME object across calls in that path.
_EVENT_REPOSITORY = InMemoryEventRepository()


def get_event_repository():
    backend = os.getenv("AICI_CACHE_BACKEND", "memory").strip().lower()

    if backend == "redis":
        return _create_redis_repository()

    return _EVENT_REPOSITORY


def reset_event_repository():
    _EVENT_REPOSITORY.clear()

    backend = os.getenv("AICI_CACHE_BACKEND", "memory").strip().lower()
    if backend == "redis":
        _create_redis_repository().clear()

    return get_event_repository()


def _create_redis_repository():
    try:
        import redis
    except ModuleNotFoundError as exc:
        raise RuntimeError(
            "AICI_CACHE_BACKEND=redis seçildi ancak redis paketi yüklü değil. "
            "requirements.txt içine redis eklenmelidir."
        ) from exc

    from app.domains.events.redis_event_repository import RedisEventRepository

    redis_url = os.getenv("AICI_REDIS_URL", "redis://redis:6379/0")
    client = redis.Redis.from_url(redis_url, decode_responses=False)
    return RedisEventRepository(client)
