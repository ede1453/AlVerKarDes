from app.domains.cache.redis_cache_repository import RedisCacheRepository


class FakeRedis:
    def __init__(self):
        self.data = {}

    def set(self, key, value):
        self.data[key] = value
        return True

    def setex(self, key, ttl, value):
        self.data[key] = value
        return True

    def get(self, key):
        return self.data.get(key)

    def delete(self, key):
        existed = key in self.data
        self.data.pop(key, None)
        return 1 if existed else 0

    def flushdb(self):
        self.data.clear()
        return True

    def info(self):
        return {"db0": {"keys": len(self.data)}}


def test_rc61_redis_cache_repository_set_get_delete():
    repo = RedisCacheRepository(FakeRedis())

    stored = repo.set("key-1", {"status": "ok"}, ttl_seconds=60)
    assert stored["key"] == "key-1"

    loaded = repo.get("key-1")
    assert loaded["value"] == {"status": "ok"}

    assert repo.delete("key-1") == 1
    assert repo.get("key-1") is None


def test_rc61_redis_cache_repository_status():
    repo = RedisCacheRepository(FakeRedis())
    repo.set("key-1", "value")

    status = repo.status()

    assert status["backend"] == "redis"
    assert status["entry_count"] == 1
