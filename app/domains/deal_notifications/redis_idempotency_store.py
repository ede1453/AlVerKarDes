from app.domains.cache.cache_namespace import build_namespaced_cache_key


class RedisIdempotencyStore:
    """SCALE-007 Part 2: Redis-backed idempotency reservations. Shares the
    same Redis instance/connection settings as the cache/rate-limit
    backends (AICI_REDIS_URL, same namespace convention via
    build_namespaced_cache_key) -- no new dependency, no new config
    surface.

    reserve() uses `SET key value NX EX ttl` -- atomic in Redis, so
    concurrent reservation attempts for the SAME (user, deal, channel,
    window) key across different worker processes never both "win": only
    one SET NX succeeds, the other sees the key already present and gets
    back the winner's notification_id. This is the actual defect being
    fixed -- InMemoryIdempotencyStore's dict was per-process (and, worse,
    its check-then-set was a real race even within one process), so two
    workers could each send their own notification for the same deal to
    the same user. TTL means a stale reservation from a crashed/slow
    request doesn't block that (user, deal, channel, window) combination
    forever -- it naturally expires and becomes reservable again.
    """

    def __init__(self, redis_client):
        self.redis_client = redis_client

    def _redis_key(self, key: str) -> str:
        return build_namespaced_cache_key(f"dealnotif-idem:{key}")

    def reserve(self, key: str, notification_id: str, ttl_seconds: int) -> str | None:
        redis_key = self._redis_key(key)
        was_set = self.redis_client.set(redis_key, notification_id, nx=True, ex=ttl_seconds)

        if was_set:
            return None

        existing = self.redis_client.get(redis_key)
        if existing is None:
            # Edge case: the reservation expired between our failed SET NX
            # and this GET. Retry once rather than fabricating a duplicate
            # result for a key that no longer exists.
            was_set = self.redis_client.set(redis_key, notification_id, nx=True, ex=ttl_seconds)
            if was_set:
                return None
            existing = self.redis_client.get(redis_key)

        return existing.decode() if isinstance(existing, bytes) else existing

    def reset(self):
        # Test-only helper, mirrors RedisRateLimitStore.reset() -- wipes
        # every dealnotif-idem:* key under the active namespace.
        pattern = build_namespaced_cache_key("dealnotif-idem:*")
        keys = list(self.redis_client.scan_iter(match=pattern, count=500))
        if keys:
            self.redis_client.delete(*keys)
