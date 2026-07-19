def test_rc612_config_settings_accepts_redis_env_variables(monkeypatch):
    monkeypatch.setenv("AICI_CACHE_BACKEND", "redis")
    monkeypatch.setenv("AICI_REDIS_URL", "redis://aici-redis-prod:6379/0")

    from app.core.config import Settings

    settings = Settings()

    assert settings.AICI_CACHE_BACKEND == "redis"
    assert settings.AICI_REDIS_URL == "redis://aici-redis-prod:6379/0"


def test_rc612_config_settings_has_safe_cache_defaults(monkeypatch):
    monkeypatch.setenv("AICI_CACHE_BACKEND", "memory")
    monkeypatch.setenv(
        "DATABASE_URL",
        "postgresql+asyncpg://postgres:12345678@localhost:5432/aici",
    )
    monkeypatch.setenv("JWT_SECRET", "local-dev-secret")
    monkeypatch.setenv("INTERNAL_SERVICE_KEY", "local-dev-internal-service-key")
    monkeypatch.delenv("AICI_REDIS_URL", raising=False)

    from app.core.config import Settings

    settings = Settings(_env_file=None)

    assert settings.AICI_CACHE_BACKEND == "memory"
    assert settings.AICI_REDIS_URL == "redis://redis:6379/0"