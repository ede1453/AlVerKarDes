from app.domains.cache.cache_service import CacheService


class DummyRepository:
    def __init__(self):
        self.values = {}

    def set(self, key, value, ttl_seconds=None):
        self.values[key] = {"key": key, "value": value, "ttl_seconds": ttl_seconds}
        return self.values[key]

    def get(self, key):
        return self.values.get(key)

    def delete(self, key):
        self.values.pop(key, None)
        return True

    def clear(self):
        self.values.clear()
        return True

    def status(self):
        return {"enabled": True, "backend": "dummy", "entry_count": len(self.values), "metadata": {}}


def test_rc61_cache_service_accepts_injected_repository():
    service = CacheService(repository=DummyRepository())

    service.set({"key": "rc61", "value": {"ok": True}, "ttl_seconds": 60})
    result = service.get("rc61")

    assert result["hit"] is True
    assert result["value"] == {"ok": True}
