from app.domains.cache.cache_repository_factory import get_cache_repository


def test_rc61_cache_repository_factory_defaults_to_memory(monkeypatch):
    monkeypatch.delenv("AICI_CACHE_BACKEND", raising=False)

    repo = get_cache_repository()

    assert repo.__class__.__name__ == "InMemoryCacheRepository"


def test_rc61_cache_repository_factory_selects_memory_explicitly(monkeypatch):
    monkeypatch.setenv("AICI_CACHE_BACKEND", "memory")

    repo = get_cache_repository()

    assert repo.__class__.__name__ == "InMemoryCacheRepository"
