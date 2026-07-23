import os

from app.domains.deal_notifications.idempotency_store import InMemoryIdempotencyStore

# SCALE-007 Part 2: mirrors app/domains/rate_limits/rate_limit_store_factory.py
# (SCALE-001) exactly -- same env var (AICI_CACHE_BACKEND), same reasoning.
# Since AICI_CACHE_BACKEND=redis is already set in .env.prod, deal
# notification idempotency reservations become Redis-backed automatically,
# no new configuration.
_default_memory_store = InMemoryIdempotencyStore()


def get_idempotency_store():
    backend = os.getenv("AICI_CACHE_BACKEND", "memory").strip().lower()

    if backend == "redis":
        return _create_redis_store()

    return _default_memory_store


def reset_memory_idempotency_store():
    _default_memory_store.reset()


def _create_redis_store():
    try:
        import redis
    except ModuleNotFoundError as exc:
        raise RuntimeError(
            "AICI_CACHE_BACKEND=redis seçildi ancak redis paketi yüklü değil. "
            "requirements.txt içine redis eklenmelidir."
        ) from exc

    from app.domains.deal_notifications.redis_idempotency_store import RedisIdempotencyStore

    redis_url = os.getenv("AICI_REDIS_URL", "redis://redis:6379/0")
    client = redis.Redis.from_url(redis_url, decode_responses=False)
    return RedisIdempotencyStore(client)
