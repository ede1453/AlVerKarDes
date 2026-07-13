from app.domains.llm_provider_health.provider_health_probe import ProviderHealthProbe


def test_provider_health_probe_marks_mock_healthy():
    status = ProviderHealthProbe().probe("mock")

    assert status.provider == "mock"
    assert status.status == "HEALTHY"
    assert status.available is True
    assert status.success_rate == 1.0


def test_provider_health_probe_marks_openai_boundary_degraded_by_default():
    status = ProviderHealthProbe().probe("openai")

    assert status.provider == "openai"
    assert status.status == "DEGRADED"
    assert status.available is False
    assert status.last_error == "PROVIDER_NOT_CONFIGURED"
