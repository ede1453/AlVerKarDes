from app.core.runtime_settings import load_runtime_settings


def test_rc611_runtime_settings_can_select_redis_backend(monkeypatch):
    monkeypatch.setenv("AICI_CACHE_BACKEND", "redis")

    settings = load_runtime_settings()

    assert settings.cache_backend == "redis"


def test_rc611_runtime_settings_accepts_redis_backend(monkeypatch):
    from app.core.runtime_settings import runtime_settings_status

    monkeypatch.setenv("AICI_CACHE_BACKEND", "redis")

    status = runtime_settings_status()

    assert status["status"] == "VALID"
    assert status["settings"]["cache_backend"] == "redis"
