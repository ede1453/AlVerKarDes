from app.domains.llm_provider_health.provider_health_engine import ProviderHealthEngine
from app.domains.llm_provider_health.provider_health_models import ProviderHealthCheckRequest


def test_provider_health_engine_summarizes_default_providers():
    summary = ProviderHealthEngine().check(
        ProviderHealthCheckRequest(
            providers=["mock", "openai", "local"],
            include_external_boundaries=True,
        )
    )

    assert summary.status == "DEGRADED"
    assert summary.healthy_count == 1
    assert summary.degraded_count >= 1


def test_provider_health_engine_marks_unknown_provider_unavailable():
    summary = ProviderHealthEngine().check(
        ProviderHealthCheckRequest(
            providers=["unknown-provider"],
            include_external_boundaries=True,
        )
    )

    assert summary.status == "UNAVAILABLE"
    assert summary.unavailable_count == 1
    assert summary.providers[0].last_error == "PROVIDER_NOT_REGISTERED"
