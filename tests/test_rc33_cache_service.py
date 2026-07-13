from app.domains.cache.cache_service import CacheService


def test_cache_service_get_or_set_returns_miss_then_hit():
    service = CacheService()
    calls = {"count": 0}

    def factory():
        calls["count"] += 1
        return {"value": "computed"}

    first = service.get_or_set(key="test:key", value_factory=factory, ttl_seconds=60)
    second = service.get_or_set(key="test:key", value_factory=factory, ttl_seconds=60)

    assert first["cache_hit"] is False
    assert second["cache_hit"] is True
    assert calls["count"] == 1


def test_cache_service_status_serializes_metrics():
    status = CacheService().status()

    assert status["enabled"] is True
    assert status["backend"] == "memory"
    assert "hit_rate" in status
