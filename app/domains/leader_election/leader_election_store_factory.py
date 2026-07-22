import os

from app.domains.leader_election.leader_election_store import InMemoryLeaderElectionStore

# SCALE-002: mirrors app/domains/rate_limits/rate_limit_store_factory.py
# exactly (itself mirroring app/domains/cache/cache_repository_factory.py)
# -- same env var (AICI_CACHE_BACKEND), same reasoning. When the deployment
# already runs with AICI_CACHE_BACKEND=redis (true in .env/.env.prod today),
# leader election becomes Redis-backed automatically, no new configuration.
_default_memory_store = InMemoryLeaderElectionStore()


def get_leader_election_store():
    backend = os.getenv("AICI_CACHE_BACKEND", "memory").strip().lower()

    if backend == "redis":
        return _create_redis_store()

    return _default_memory_store


def reset_memory_leader_election_store():
    _default_memory_store.reset()


def _create_redis_store():
    try:
        import redis
    except ModuleNotFoundError as exc:
        raise RuntimeError(
            "AICI_CACHE_BACKEND=redis seçildi ancak redis paketi yüklü değil. "
            "requirements.txt içine redis eklenmelidir."
        ) from exc

    from app.domains.leader_election.redis_leader_election_store import RedisLeaderElectionStore

    redis_url = os.getenv("AICI_REDIS_URL", "redis://redis:6379/0")
    client = redis.Redis.from_url(redis_url, decode_responses=False)
    return RedisLeaderElectionStore(client)
