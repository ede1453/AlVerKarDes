from app.core.runtime_settings import runtime_settings_status


def test_rc63_runtime_settings_does_not_leak_cache_namespace_secret(monkeypatch):
    monkeypatch.setenv("AICI_CACHE_NAMESPACE", "aici-test")

    status = runtime_settings_status()

    text = str(status)
    assert "AICI_CACHE_NAMESPACE" not in text
