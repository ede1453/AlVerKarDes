from app.domains.cache.cache_key_builder import CacheKeyBuilder


def test_cache_key_builder_is_stable_for_same_payload_order():
    builder = CacheKeyBuilder()

    first = builder.build(namespace="recommendation", payload={"b": 2, "a": 1})
    second = builder.build(namespace="recommendation", payload={"a": 1, "b": 2})

    assert first == second
    assert first.startswith("recommendation:")
