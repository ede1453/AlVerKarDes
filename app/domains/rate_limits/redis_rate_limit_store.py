from datetime import datetime, timedelta, timezone

from app.domains.cache.cache_namespace import build_namespaced_cache_key
from app.domains.rate_limits.rate_limit_models import RateLimitUsage


class RedisRateLimitStore:
    """SCALE-001: Redis-backed rate limit counters. Shares the same Redis
    instance/connection settings as the cache backend (AICI_REDIS_URL,
    same namespace convention via build_namespaced_cache_key) -- no new
    dependency, no new config surface.

    Standard atomic fixed-window counter pattern: INCR is atomic in Redis,
    so concurrent requests hitting DIFFERENT worker processes/instances
    still increment the SAME counter -- this is the actual defect being
    fixed (InMemoryRateLimitStore's dict was per-process, so a limit like
    "5 password-reset requests per 15 minutes" was actually "5 x worker
    count" under multiple workers). See WIKI_ROOT ADR-017/ADR-018.
    """

    def __init__(self, redis_client):
        self.redis_client = redis_client

    def _redis_key(self, key: str, scope: str) -> str:
        return build_namespaced_cache_key(f"ratelimit:{scope}:{key}")

    def increment(self, *, key: str, scope: str, window_seconds: int) -> RateLimitUsage:
        redis_key = self._redis_key(key, scope)
        count = self.redis_client.incr(redis_key)

        if count == 1:
            # First hit in a new window -- arm the expiry so the counter
            # resets on its own; Redis handles cleanup, no separate reset
            # job needed.
            self.redis_client.expire(redis_key, window_seconds)
            ttl = window_seconds
        else:
            ttl = self.redis_client.ttl(redis_key)
            if ttl is None or ttl < 0:
                # Edge case: the key exists but has no TTL (process crashed
                # between INCR and EXPIRE on the very first hit). Fail safe
                # by re-arming the window rather than leaving a counter
                # that never resets.
                self.redis_client.expire(redis_key, window_seconds)
                ttl = window_seconds

        now = datetime.now(timezone.utc)
        window_started_at = now - timedelta(seconds=window_seconds - ttl)

        return RateLimitUsage(
            key=key,
            scope=scope,
            count=count,
            window_started_at=window_started_at,
        )

    def reset(self):
        # Test-only helper, mirrors RedisCacheRepository.clear() -- wipes
        # every ratelimit:* key under the active namespace.
        pattern = build_namespaced_cache_key("ratelimit:*")
        keys = list(self.redis_client.scan_iter(match=pattern, count=500))
        if keys:
            self.redis_client.delete(*keys)
