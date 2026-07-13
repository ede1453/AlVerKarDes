from app.domains.cache.redis_cache_repository import RedisCacheRepository


class FakeRedisScan:
    def __init__(self):
        self.data = {}
        self.deleted_keys = []
        self.flushdb_called = False

    def set(self, key, value):
        self.data[key] = value
        return True

    def setex(self, key, ttl, value):
        self.data[key] = value
        return True

    def get(self, key):
        return self.data.get(key)

    def delete(self, *keys):
        self.deleted_keys.extend(keys)
        count = 0
        for key in keys:
            if key in self.data:
                count += 1
                self.data.pop(key, None)
        return count

    def scan_iter(self, match=None, count=None):
        import fnmatch

        for key in list(self.data.keys()):
            if match is None or fnmatch.fnmatch(key, match):
                yield key

    def flushdb(self):
        self.flushdb_called = True
        self.data.clear()
        return True

    def info(self):
        return {"db0": {"keys": len(self.data)}}


def test_rc64_redis_clear_deletes_only_current_namespace(monkeypatch):
    monkeypatch.setenv("AICI_CACHE_NAMESPACE", "aici-test")
    fake = FakeRedisScan()
    repo = RedisCacheRepository(fake)

    repo.set("deal:1", {"status": "current"}, ttl_seconds=60)
    fake.data["other:deal:2"] = "{\"key\": \"deal:2\", \"value\": \"other\"}"

    deleted = repo.clear()

    assert deleted == 1
    assert "aici-test:deal:1" not in fake.data
    assert "other:deal:2" in fake.data
    assert fake.flushdb_called is False


def test_rc64_redis_clear_returns_zero_when_namespace_empty(monkeypatch):
    monkeypatch.setenv("AICI_CACHE_NAMESPACE", "aici-empty")
    fake = FakeRedisScan()
    repo = RedisCacheRepository(fake)

    fake.data["other:deal:2"] = "{\"key\": \"deal:2\", \"value\": \"other\"}"

    deleted = repo.clear()

    assert deleted == 0
    assert "other:deal:2" in fake.data
    assert fake.flushdb_called is False
