from app.domains.cache.redis_cache_repository import RedisCacheRepository


class FakeRedis:
    def __init__(self):
        self.data = {}
        self.last_set_key = None
        self.last_get_key = None
        self.last_delete_key = None

    def set(self, key, value):
        self.last_set_key = key
        self.data[key] = value
        return True

    def setex(self, key, ttl, value):
        self.last_set_key = key
        self.data[key] = value
        return True

    def get(self, key):
        self.last_get_key = key
        return self.data.get(key)

    def delete(self, key):
        self.last_delete_key = key
        existed = key in self.data
        self.data.pop(key, None)
        return 1 if existed else 0

    def flushdb(self):
        self.data.clear()
        return True

    def info(self):
        return {"db0": {"keys": len(self.data)}}


def test_rc63_redis_repository_keeps_public_key_stable(monkeypatch):
    monkeypatch.setenv("AICI_CACHE_NAMESPACE", "aici-test")
    fake = FakeRedis()
    repo = RedisCacheRepository(fake)

    result = repo.set("deal:1", {"status": "ok"}, ttl_seconds=60)

    assert result["key"] == "deal:1"


def test_rc63_redis_repository_should_namespace_internal_redis_key(monkeypatch):
    monkeypatch.setenv("AICI_CACHE_NAMESPACE", "aici-test")
    fake = FakeRedis()
    repo = RedisCacheRepository(fake)

    repo.set("deal:1", {"status": "ok"}, ttl_seconds=60)

    assert fake.last_set_key == "aici-test:deal:1"


def test_rc63_redis_repository_should_read_namespaced_key(monkeypatch):
    monkeypatch.setenv("AICI_CACHE_NAMESPACE", "aici-test")
    fake = FakeRedis()
    repo = RedisCacheRepository(fake)

    repo.set("deal:1", {"status": "ok"}, ttl_seconds=60)
    loaded = repo.get("deal:1")

    assert loaded["value"] == {"status": "ok"}
    assert fake.last_get_key == "aici-test:deal:1"


def test_rc63_redis_repository_should_delete_namespaced_key(monkeypatch):
    monkeypatch.setenv("AICI_CACHE_NAMESPACE", "aici-test")
    fake = FakeRedis()
    repo = RedisCacheRepository(fake)

    repo.set("deal:1", {"status": "ok"}, ttl_seconds=60)
    deleted = repo.delete("deal:1")

    assert deleted == 1
    assert fake.last_delete_key == "aici-test:deal:1"
