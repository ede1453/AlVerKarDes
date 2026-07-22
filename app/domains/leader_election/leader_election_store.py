from datetime import datetime, timedelta, timezone


class InMemoryLeaderElectionStore:
    """Process-local leader-election lock. Only correct within a single
    worker process -- kept as the default/test fallback (mirrors
    InMemoryRateLimitStore's role for RateLimitEngine, SCALE-001). The real
    multi-worker-safe path is RedisLeaderElectionStore, selected via
    get_leader_election_store() when AICI_CACHE_BACKEND=redis.
    """

    def __init__(self):
        self._state: dict[str, dict] = {}

    def _current(self, key: str) -> dict:
        return self._state.get(key, {"leader_id": None, "lease_expires_at": None})

    def status(self, key: str) -> dict:
        return dict(self._current(key))

    def acquire(self, *, key: str, worker_id: str, lease_seconds: int) -> dict:
        current = self._current(key)

        if current["leader_id"] is not None and current["leader_id"] != worker_id:
            return {
                "acquired": False,
                "reason": "LEADER_ALREADY_ACTIVE",
                "leader_id": current["leader_id"],
                "lease_expires_at": current["lease_expires_at"],
            }

        lease_expires_at = (
            datetime.now(timezone.utc) + timedelta(seconds=lease_seconds)
        ).isoformat()
        self._state[key] = {"leader_id": worker_id, "lease_expires_at": lease_expires_at}

        return {
            "acquired": True,
            "reason": "LEADERSHIP_ACQUIRED",
            "leader_id": worker_id,
            "lease_expires_at": lease_expires_at,
        }

    def renew(self, *, key: str, worker_id: str, lease_seconds: int) -> dict:
        current = self._current(key)

        if current["leader_id"] != worker_id:
            return {
                "renewed": False,
                "reason": "NOT_CURRENT_LEADER",
                "leader_id": current["leader_id"],
                "lease_expires_at": current["lease_expires_at"],
            }

        lease_expires_at = (
            datetime.now(timezone.utc) + timedelta(seconds=lease_seconds)
        ).isoformat()
        self._state[key]["lease_expires_at"] = lease_expires_at

        return {
            "renewed": True,
            "reason": "LEADERSHIP_RENEWED",
            "leader_id": worker_id,
            "lease_expires_at": lease_expires_at,
        }

    def release(self, *, key: str, worker_id: str) -> dict:
        current = self._current(key)

        if current["leader_id"] != worker_id:
            return {
                "released": False,
                "reason": "NOT_CURRENT_LEADER",
                "leader_id": current["leader_id"],
            }

        self._state[key] = {"leader_id": None, "lease_expires_at": None}

        return {
            "released": True,
            "reason": "LEADERSHIP_RELEASED",
            "leader_id": None,
            "lease_expires_at": None,
        }

    def reset(self):
        self._state.clear()
