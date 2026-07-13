from app.domains.cache.cache_key_builder import CacheKeyBuilder
from app.domains.cache.cache_repository_factory import get_cache_repository
from app.domains.cache.cache_serializer import (
    serialize_cache_entry,
    serialize_cache_lookup,
    serialize_cache_status,
)


class CacheService:
    def __init__(self, repository=None, key_builder: CacheKeyBuilder | None = None):
        self.repository = repository or get_cache_repository()
        self.key_builder = key_builder or CacheKeyBuilder()

    def build_key(self, payload: dict):
        return {
            "key": self.key_builder.build(
                namespace=payload.get("namespace", "default"),
                payload=payload.get("payload", {}),
            )
        }

    def get(self, payload):
        key = payload["key"] if isinstance(payload, dict) else payload
        return serialize_cache_lookup(self.repository.get(key), key=key)

    def set(self, payload: dict):
        entry = self.repository.set(
            key=payload["key"],
            value=payload.get("value", {}),
            ttl_seconds=payload.get("ttl_seconds", 300),
        )
        return serialize_cache_entry(entry)

    def get_or_set(self, *, key: str, value_factory, ttl_seconds: int):
        result = self.repository.get(key)
        if result.hit:
            return {
                "cache_hit": True,
                "key": key,
                "value": result.value,
                "metadata": result.metadata,
            }

        value = value_factory()
        entry = self.repository.set(key=key, value=value, ttl_seconds=ttl_seconds)
        return {
            "cache_hit": False,
            "key": key,
            "value": entry.value,
            "metadata": {
                "created_at": entry.created_at.isoformat(),
                "expires_at": entry.expires_at.isoformat(),
                "ttl_seconds": entry.ttl_seconds,
            },
        }

    def status(self):
        return serialize_cache_status(self.repository.status())

    def clear(self):
        self.repository.clear()
        return self.status()