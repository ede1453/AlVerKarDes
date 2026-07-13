import os
from dataclasses import dataclass, field

_ALLOWED_ENVIRONMENTS = {"local", "test", "staging", "production"}
_ALLOWED_LLM_PROVIDERS = {"mock", "openai", "local"}
_ALLOWED_CACHE_BACKENDS = {"memory", "redis"}
_ALLOWED_NOTIFICATION_PROVIDERS = {"mock", "external"}


@dataclass(frozen=True)
class RuntimeSettings:
    environment: str = "local"
    api_version: str = "v1"
    default_llm_provider: str = "mock"
    cache_backend: str = "memory"
    notification_provider: str = "mock"
    external_providers_enabled: bool = False
    debug: bool = False
    metadata: dict = field(default_factory=dict)


def _bool_from_value(value: str | None, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "y", "on"}


def _bool_from_env(name: str, default: bool = False) -> bool:
    return _bool_from_value(os.getenv(name), default)


def _bool_from_env_any(names: list[str], default: bool = False) -> bool:
    for name in names:
        value = os.getenv(name)
        if value is not None:
            return _bool_from_value(value, default)
    return default


def _read_env(name: str, default: str) -> str:
    return os.getenv(name, default).strip()


def load_runtime_settings() -> RuntimeSettings:
    environment = _read_env("AICI_ENVIRONMENT", "local")
    default_llm_provider = _read_env("AICI_DEFAULT_LLM_PROVIDER", "mock")
    cache_backend = _read_env("AICI_CACHE_BACKEND", "memory")
    notification_provider = _read_env("AICI_NOTIFICATION_PROVIDER", "mock")

    return RuntimeSettings(
        environment=environment,
        api_version=_read_env("AICI_API_VERSION", "v1"),
        default_llm_provider=default_llm_provider,
        cache_backend=cache_backend,
        notification_provider=notification_provider,
        external_providers_enabled=_bool_from_env_any(
            [
                "AICI_EXTERNAL_PROVIDERS_ENABLED",
                "AICI_EXTERNAL_PROVIDER_ENABLED",
            ],
            False,
        ),
        debug=_bool_from_env("AICI_DEBUG", False),
        metadata={"settings_version": "runtime_settings_v1"},
    )


def validate_runtime_settings(settings: RuntimeSettings) -> list[dict]:
    issues: list[dict] = []

    if settings.environment not in _ALLOWED_ENVIRONMENTS:
        issues.append(
            {
                "field": "environment",
                "code": "INVALID_ENVIRONMENT",
                "message": "AICI_ENVIRONMENT local, test, staging veya production olmalıdır.",
                "value": settings.environment,
            }
        )

    if settings.default_llm_provider not in _ALLOWED_LLM_PROVIDERS:
        issues.append(
            {
                "field": "default_llm_provider",
                "code": "INVALID_LLM_PROVIDER",
                "message": "AICI_DEFAULT_LLM_PROVIDER mock, openai veya local olmalıdır.",
                "value": settings.default_llm_provider,
            }
        )

    if settings.cache_backend not in _ALLOWED_CACHE_BACKENDS:
        issues.append(
            {
                "field": "cache_backend",
                "code": "INVALID_CACHE_BACKEND",
                "message": "AICI_CACHE_BACKEND memory veya redis olmalıdır.",
                "value": settings.cache_backend,
            }
        )

    if settings.notification_provider not in _ALLOWED_NOTIFICATION_PROVIDERS:
        issues.append(
            {
                "field": "notification_provider",
                "code": "INVALID_NOTIFICATION_PROVIDER",
                "message": "AICI_NOTIFICATION_PROVIDER mock veya external olmalıdır.",
                "value": settings.notification_provider,
            }
        )

    if settings.environment == "production" and settings.debug:
        issues.append(
            {
                "field": "debug",
                "code": "DEBUG_ENABLED_IN_PRODUCTION",
                "message": "Production ortamında debug açık olmamalıdır.",
                "value": settings.debug,
            }
        )

    if settings.environment == "production" and settings.default_llm_provider == "mock":
        issues.append(
            {
                "field": "default_llm_provider",
                "code": "MOCK_PROVIDER_IN_PRODUCTION",
                "message": "Production ortamında varsayılan LLM provider mock olmamalıdır.",
                "value": settings.default_llm_provider,
            }
        )

    if not settings.external_providers_enabled and settings.default_llm_provider in {"openai", "local"}:
        issues.append(
            {
                "field": "external_providers_enabled",
                "code": "EXTERNAL_PROVIDER_SELECTED_BUT_DISABLED",
                "message": "Harici provider seçilmiş ancak AICI_EXTERNAL_PROVIDERS_ENABLED açık değil.",
                "value": settings.external_providers_enabled,
            }
        )

    return issues


def runtime_settings_status(settings: RuntimeSettings | None = None) -> dict:
    settings = settings or load_runtime_settings()
    issues = validate_runtime_settings(settings)

    return {
        "status": "VALID" if not issues else "INVALID",
        "settings": {
            "environment": settings.environment,
            "api_version": settings.api_version,
            "default_llm_provider": settings.default_llm_provider,
            "cache_backend": settings.cache_backend,
            "notification_provider": settings.notification_provider,
            "external_providers_enabled": settings.external_providers_enabled,
            "debug": settings.debug,
            "metadata": settings.metadata,
        },
        "issue_count": len(issues),
        "issues": issues,
    }
