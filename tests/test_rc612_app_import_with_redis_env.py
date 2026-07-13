def test_rc612_app_import_does_not_fail_with_redis_env(monkeypatch):
    monkeypatch.setenv("AICI_CACHE_BACKEND", "redis")
    monkeypatch.setenv("AICI_REDIS_URL", "redis://aici-redis-prod:6379/0")

    from app.main import app

    assert app is not None
