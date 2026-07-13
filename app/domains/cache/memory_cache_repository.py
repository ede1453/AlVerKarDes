from datetime import datetime, timedelta, timezone

from app.domains.cache.cache_models import CacheEntry, CacheLookupResult, CacheStatus
from app.domains.cache.cache_repository import CacheRepository


class MemoryCacheRepository(CacheRepository):
    backend = "memory"

    def __init__(self):
        self._entries: dict[str, CacheEntry] = {}
        self.hit_count = 0
        self.miss_count = 0

    def get(self, key: str) -> CacheLookupResult:
        entry = self._entries.get(key)

        if entry is None:
            self.miss_count += 1
            return CacheLookupResult(hit=False, key=key, value=None, metadata={"reason": "CACHE_MISS"})

        now = datetime.now(timezone.utc)
        if now >= entry.expires_at:
            self._entries.pop(key, None)
            self.miss_count += 1
            return CacheLookupResult(hit=False, key=key, value=None, metadata={"reason": "CACHE_EXPIRED"})

        self.hit_count += 1
        return CacheLookupResult(
            hit=True,
            key=key,
            value=entry.value,
            metadata={
                "created_at": entry.created_at.isoformat(),
                "expires_at": entry.expires_at.isoformat(),
                "ttl_seconds": entry.ttl_seconds,
            },
        )

    def set(self, *, key: str, value: dict, ttl_seconds: int) -> CacheEntry:
        now = datetime.now(timezone.utc)
        ttl_seconds = max(1, int(ttl_seconds))

        entry = CacheEntry(
            key=key,
            value=value,
            ttl_seconds=ttl_seconds,
            created_at=now,
            expires_at=now + timedelta(seconds=ttl_seconds),
        )
        self._entries[key] = entry
        return entry

    def delete(self, key: str) -> bool:
        return self._entries.pop(key, None) is not None

    def clear(self):
        self._entries.clear()
        self.hit_count = 0
        self.miss_count = 0

    def status(self) -> CacheStatus:
        self._purge_expired()

        total = self.hit_count + self.miss_count
        hit_rate = 0.0 if total == 0 else self.hit_count / total
        miss_rate = 0.0 if total == 0 else self.miss_count / total

        return CacheStatus(
            enabled=True,
            backend=self.backend,
            entry_count=len(self._entries),
            hit_count=self.hit_count,
            miss_count=self.miss_count,
            hit_rate=round(hit_rate, 4),
            miss_rate=round(miss_rate, 4),
            metadata={"ttl_policy": "per_entry"},
        )

    def _purge_expired(self):
        now = datetime.now(timezone.utc)
        expired_keys = [
            key for key, entry in self._entries.items()
            if now >= entry.expires_at
        ]
        for key in expired_keys:
            self._entries.pop(key, None)


class InMemoryCacheRepository(MemoryCacheRepository):
    pass
