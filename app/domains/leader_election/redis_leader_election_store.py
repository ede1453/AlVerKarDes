from datetime import datetime, timedelta, timezone

from app.domains.cache.cache_namespace import build_namespaced_cache_key

# Compare-and-swap Lua scripts -- the standard Redis-documented pattern for
# safe distributed-lock acquire/renew/release (avoids a worker accidentally
# renewing/releasing a lock that has since expired and been re-acquired by
# a different worker). Single-Redis-node lock: no Redlock multi-node quorum
# needed since this deployment runs one Redis instance -- see WIKI_ROOT
# ADR-017 SCALE-002 Sonuç Raporu for the reasoning.
#
# acquire uses CAS rather than a plain SET NX because the original
# InMemoryLeaderElectionStore contract (leader_election_store.py) lets the
# CURRENT leader call acquire() again idempotently (leader_id != worker_id
# is the only block condition) -- a bare NX would reject that self-reacquire
# since the key already exists, silently changing behavior between backends.
_ACQUIRE_SCRIPT = """
local current = redis.call('get', KEYS[1])
if current == false or current == ARGV[1] then
    redis.call('set', KEYS[1], ARGV[1], 'EX', ARGV[2])
    return 1
else
    return 0
end
"""

_RENEW_SCRIPT = """
if redis.call('get', KEYS[1]) == ARGV[1] then
    return redis.call('expire', KEYS[1], ARGV[2])
else
    return 0
end
"""

_RELEASE_SCRIPT = """
if redis.call('get', KEYS[1]) == ARGV[1] then
    return redis.call('del', KEYS[1])
else
    return 0
end
"""


class RedisLeaderElectionStore:
    def __init__(self, redis_client):
        self.redis_client = redis_client

    def _redis_key(self, key: str) -> str:
        return build_namespaced_cache_key(f"leader:{key}")

    def _decode(self, value):
        if value is None:
            return None
        if isinstance(value, bytes):
            return value.decode("utf-8")
        return value

    def status(self, key: str) -> dict:
        redis_key = self._redis_key(key)
        leader_id = self._decode(self.redis_client.get(redis_key))

        if leader_id is None:
            return {"leader_id": None, "lease_expires_at": None}

        ttl = self.redis_client.ttl(redis_key)
        lease_expires_at = None
        if ttl is not None and ttl >= 0:
            lease_expires_at = (
                datetime.now(timezone.utc) + timedelta(seconds=ttl)
            ).isoformat()

        return {"leader_id": leader_id, "lease_expires_at": lease_expires_at}

    def acquire(self, *, key: str, worker_id: str, lease_seconds: int) -> dict:
        redis_key = self._redis_key(key)
        # Atomic: succeeds if the key is free OR already owned by this same
        # worker_id (idempotent self-reacquire, matches in-memory contract).
        # Redis's own TTL (ex=lease_seconds) expires an abandoned lock
        # automatically -- unlike the in-memory version, this is a real fix.
        acquired = self.redis_client.eval(_ACQUIRE_SCRIPT, 1, redis_key, worker_id, lease_seconds)

        if not acquired:
            current = self.status(key)
            return {
                "acquired": False,
                "reason": "LEADER_ALREADY_ACTIVE",
                "leader_id": current["leader_id"],
                "lease_expires_at": current["lease_expires_at"],
            }

        lease_expires_at = (
            datetime.now(timezone.utc) + timedelta(seconds=lease_seconds)
        ).isoformat()

        return {
            "acquired": True,
            "reason": "LEADERSHIP_ACQUIRED",
            "leader_id": worker_id,
            "lease_expires_at": lease_expires_at,
        }

    def renew(self, *, key: str, worker_id: str, lease_seconds: int) -> dict:
        redis_key = self._redis_key(key)
        renewed = self.redis_client.eval(_RENEW_SCRIPT, 1, redis_key, worker_id, lease_seconds)

        if not renewed:
            current = self.status(key)
            return {
                "renewed": False,
                "reason": "NOT_CURRENT_LEADER",
                "leader_id": current["leader_id"],
                "lease_expires_at": current["lease_expires_at"],
            }

        lease_expires_at = (
            datetime.now(timezone.utc) + timedelta(seconds=lease_seconds)
        ).isoformat()

        return {
            "renewed": True,
            "reason": "LEADERSHIP_RENEWED",
            "leader_id": worker_id,
            "lease_expires_at": lease_expires_at,
        }

    def release(self, *, key: str, worker_id: str) -> dict:
        redis_key = self._redis_key(key)
        released = self.redis_client.eval(_RELEASE_SCRIPT, 1, redis_key, worker_id)

        if not released:
            current = self.status(key)
            return {
                "released": False,
                "reason": "NOT_CURRENT_LEADER",
                "leader_id": current["leader_id"],
            }

        return {
            "released": True,
            "reason": "LEADERSHIP_RELEASED",
            "leader_id": None,
            "lease_expires_at": None,
        }

    def reset(self):
        pattern = build_namespaced_cache_key("leader:*")
        keys = list(self.redis_client.scan_iter(match=pattern, count=500))
        if keys:
            self.redis_client.delete(*keys)
