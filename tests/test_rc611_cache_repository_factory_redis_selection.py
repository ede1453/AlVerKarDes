import pytest

from app.domains.cache.cache_repository_factory import get_cache_repository


class FakeRedisModule:
    class Redis:
        @staticmethod
        def from_url(url, decode_responses=False):
            return FakeRedisClient(url=url, decode_responses=decode_responses)


class FakeRedisClient:
    def __init__(self, url, decode_responses=False):
        self.url = url
        self.decode_responses = decode_responses
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
        self.data.pop(key, None)
        return 1

    def flushdb(self):
        self.data.clear()
        return True

    def info(self):
        return {"db0": {"keys": len(self.data)}}


def test_rc611_cache_repository_factory_selects_redis_with_fake_module(monkeypatch):
    import sys

    monkeypatch.setenv("AICI_CACHE_BACKEND", "redis")
    monkeypatch.setenv("AICI_REDIS_URL", "redis://example-redis:6379/0")
    monkeypatch.setitem(sys.modules, "redis", FakeRedisModule)

    repo = get_cache_repository()

    assert repo.__class__.__name__ == "RedisCacheRepository"
    assert repo.redis_client.url == "redis://example-redis:6379/0"


def test_rc611_cache_repository_factory_raises_clear_error_if_redis_package_missing(monkeypatch):
    import sys

    monkeypatch.setenv("AICI_CACHE_BACKEND", "redis")

    # Setting sys.modules[name] = None is the standard way to force
    # ModuleNotFoundError on `import name`, regardless of whether the real
    # package is actually installed (unlike `del sys.modules[name]`, which
    # only clears the cache and lets a real import succeed if the package is
    # present -- the previous version of this test used `del` + a manual
    # __import__ probe and self-skipped whenever redis was installed, which
    # is always the case here since it's a real requirements.txt dependency.
    # That meant the "missing package" branch in cache_repository_factory.py
    # had zero real test coverage. This forces the branch every time.
    monkeypatch.setitem(sys.modules, "redis", None)

    with pytest.raises(RuntimeError, match="redis paketi yüklü değil"):
        get_cache_repository()