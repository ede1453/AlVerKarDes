from app.domains.llm_provider_health.provider_health_service import ProviderHealthService


def test_provider_health_service_serializes_summary():
    data = ProviderHealthService().check(
        {
            "providers": ["mock"],
            "include_external_boundaries": True,
        }
    )

    assert data["status"] == "HEALTHY"
    assert data["healthy_count"] == 1
    assert data["providers"][0]["provider"] == "mock"
