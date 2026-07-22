import os

from app.domains.rate_limits.rate_limit_store import InMemoryRateLimitStore

# SCALE-001: mirrors app/domains/cache/cache_repository_factory.py exactly
# -- same env var (AICI_CACHE_BACKEND), same reasoning. When the deployment
# already runs with AICI_CACHE_BACKEND=redis (true in .env/.env.prod today),
# rate limiting becomes Redis-backed automatically, no new configuration.
_default_memory_store = InMemoryRateLimitStore()


def get_rate_limit_store():
    backend = os.getenv("AICI_CACHE_BACKEND", "memory").strip().lower()

    if backend == "redis":
        return _create_redis_store()

    return _default_memory_store


def reset_memory_rate_limit_store():
    _default_memory_store.reset()


def _create_redis_store():
    try:
        import redis
    except ModuleNotFoundError as exc:
        raise RuntimeError(
            "AICI_CACHE_BACKEND=redis seçildi ancak redis paketi yüklü değil. "
            "requirements.txt içine redis eklenmelidir."
        ) from exc

    from app.domains.rate_limits.redis_rate_limit_store import RedisRateLimitStore

    redis_url = os.getenv("AICI_REDIS_URL", "redis://redis:6379/0")
    client = redis.Redis.from_url(redis_url, decode_responses=False)
    return RedisRateLimitStore(client)
