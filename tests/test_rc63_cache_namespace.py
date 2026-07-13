from app.domains.cache.cache_namespace import (
    build_namespaced_cache_key,
    get_cache_namespace,
    normalize_cache_namespace,
    strip_cache_namespace,
)


def test_rc63_normalize_cache_namespace():
    assert normalize_cache_namespace(" AICI Prod ") == "aici-prod"
    assert normalize_cache_namespace("AICI_TEST") == "aici-test"
    assert normalize_cache_namespace("aici:prod") == "aici:prod"


def test_rc63_build_namespaced_cache_key():
    assert build_namespaced_cache_key("product:1", "aici-test") == "aici-test:product:1"


def test_rc63_build_namespaced_cache_key_is_idempotent():
    assert build_namespaced_cache_key("aici-test:product:1", "aici-test") == "aici-test:product:1"


def test_rc63_strip_cache_namespace():
    assert strip_cache_namespace("aici-test:product:1", "aici-test") == "product:1"
    assert strip_cache_namespace("other:product:1", "aici-test") == "other:product:1"


def test_rc63_get_cache_namespace_reads_env(monkeypatch):
    monkeypatch.setenv("AICI_CACHE_NAMESPACE", "AICI Test")
    assert get_cache_namespace() == "aici-test"
