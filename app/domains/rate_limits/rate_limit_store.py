from datetime import datetime, timedelta, timezone

from app.domains.rate_limits.rate_limit_models import RateLimitUsage


class InMemoryRateLimitStore:
    def __init__(self):
        self._usage: dict[tuple[str, str], RateLimitUsage] = {}

    def increment(self, *, key: str, scope: str, window_seconds: int) -> RateLimitUsage:
        now = datetime.now(timezone.utc)
        store_key = (key, scope)
        current = self._usage.get(store_key)

        if current is None or now >= current.window_started_at + timedelta(seconds=window_seconds):
            current = RateLimitUsage(
                key=key,
                scope=scope,
                count=0,
                window_started_at=now,
            )

        current.count += 1
        self._usage[store_key] = current

        return current

    def reset(self):
        self._usage.clear()
