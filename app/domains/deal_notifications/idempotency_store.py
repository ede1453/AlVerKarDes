import threading


class InMemoryIdempotencyStore:
    """Plain in-memory test double (SCALE-007 Part 2 -- mirrors
    InMemoryRateLimitStore's role as the default/test fallback). A
    `threading.Lock` guards the check-then-set: reserve_idempotency_key()
    is exposed via a SYNC FastAPI endpoint, which FastAPI runs in a
    threadpool -- multiple real OS threads can call this concurrently
    within a single process, so even the in-memory path needs real
    mutual exclusion (the original code's `dict.get()` then `dict[key]=`
    was a genuine TOCTOU race, not just a "different worker process"
    problem)."""

    def __init__(self):
        self._reservations: dict[str, str] = {}
        self._lock = threading.Lock()

    def reserve(self, key: str, notification_id: str, ttl_seconds: int) -> str | None:
        with self._lock:
            existing = self._reservations.get(key)
            if existing is not None:
                return existing
            self._reservations[key] = notification_id
            return None

    def reset(self):
        with self._lock:
            self._reservations.clear()
