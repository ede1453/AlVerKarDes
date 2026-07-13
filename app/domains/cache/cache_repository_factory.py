import os

from app.domains.cache.memory_cache_repository import InMemoryCacheRepository
from app.domains.cache.redis_cache_repository import RedisCacheRepository

_default_memory_cache_repository = InMemoryCacheRepository()


def get_cache_repository():
    backend = os.getenv("AICI_CACHE_BACKEND", "memory").strip().lower()

    if backend == "redis":
        return _create_redis_repository()

    return _default_memory_cache_repository


def reset_memory_cache_repository():
    _default_memory_cache_repository.clear()


def _create_redis_repository():
    try:
        import redis
    except ModuleNotFoundError as exc:
        raise RuntimeError(
            "AICI_CACHE_BACKEND=redis seçildi ancak redis paketi yüklü değil. "
            "requirements.txt içine redis eklenmelidir."
        ) from exc

    redis_url = os.getenv("AICI_REDIS_URL", "redis://redis:6379/0")
    client = redis.Redis.from_url(redis_url, decode_responses=False)
    return RedisCacheRepository(client)
