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
    monkeypatch.delitem(sys.modules, "redis", raising=False)

    # EÃ„Å¸er redis gerÃƒÂ§ekten kuruluysa bu test skip edilir; lokal/CI ortamÃ„Â±nda kurulu deÃ„Å¸ilse hata mesajÃ„Â±nÃ„Â± doÃ„Å¸rular.
    try:
        __import__("redis")
    except ModuleNotFoundError:
        with pytest.raises(RuntimeError, match="redis paketi yÃƒÂ¼klÃƒÂ¼ deÃ„Å¸il"):
            get_cache_repository()
    else:
        pytest.skip("redis paketi ortamda kurulu; missing-package senaryosu atlandÃ„Â±.")