def test_rc613_config_settings_uses_existing_uppercase_field_style():
    from app.core.config import Settings

    settings = Settings()

    assert hasattr(settings, "APP_NAME")
    assert hasattr(settings, "DATABASE_URL")
    assert hasattr(settings, "AICI_CACHE_BACKEND")
    assert hasattr(settings, "AICI_REDIS_URL")


def test_rc613_config_settings_does_not_require_lowercase_aliases():
    from app.core.config import Settings

    settings = Settings()

    assert not hasattr(settings, "aici_cache_backend")
    assert not hasattr(settings, "aici_redis_url")
