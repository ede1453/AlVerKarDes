import json
from datetime import datetime, timezone
from typing import Any

from app.domains.cache.cache_namespace import build_namespaced_cache_key, get_cache_namespace


class RedisCacheRepository:
    def __init__(self, redis_client):
        self.redis_client = redis_client

    def set(self, key: str, value: Any, ttl_seconds: int | None = None):
        created_at = datetime.now(timezone.utc).isoformat()
        envelope = {
            "key": key,
            "value": value,
            "ttl_seconds": ttl_seconds,
            "created_at": created_at,
        }

        serialized = json.dumps(envelope, ensure_ascii=False)
        redis_key = build_namespaced_cache_key(key)
        
        if ttl_seconds is None:
            self.redis_client.set(redis_key, serialized)
        else:
            self.redis_client.setex(redis_key, ttl_seconds, serialized)

        return envelope

    def get(self, key: str):
        raw = self.redis_client.get(build_namespaced_cache_key(key))
        if raw is None:
            return None

        if isinstance(raw, bytes):
            raw = raw.decode("utf-8")

        return json.loads(raw)

    def delete(self, key: str):
        return self.redis_client.delete(build_namespaced_cache_key(key))

    def clear(self):
        namespace = get_cache_namespace()
        pattern = f"{namespace}:*"
        keys = list(self.redis_client.scan_iter(match=pattern, count=500))

        if not keys:
            return 0

        return self.redis_client.delete(*keys)

    def status(self):
        info = {}
        try:
            info = self.redis_client.info()
        except Exception:
            info = {}

        return {
            "enabled": True,
            "backend": "redis",
            "entry_count": info.get("db0", {}).get("keys", 0) if isinstance(info.get("db0"), dict) else 0,
            "metadata": {
                "cache_repository": "redis_cache_repository_v1",
                "redis_available": True,
            },
        }
