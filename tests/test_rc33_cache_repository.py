from app.domains.cache.memory_cache_repository import MemoryCacheRepository


def test_memory_cache_repository_set_and_get_hit():
    repository = MemoryCacheRepository()
    repository.set(key="test:key", value={"answer": 42}, ttl_seconds=60)

    result = repository.get("test:key")

    assert result.hit is True
    assert result.value == {"answer": 42}
    assert repository.status().hit_count == 1


def test_memory_cache_repository_get_miss():
    repository = MemoryCacheRepository()
    result = repository.get("missing:key")

    assert result.hit is False
    assert result.value is None
    assert repository.status().miss_count == 1
