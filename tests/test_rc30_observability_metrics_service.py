from app.domains.observability.metrics_service import ObservabilityMetricsService


def test_observability_metrics_service_serializes_snapshot():
    data = ObservabilityMetricsService().snapshot(
        {
            "providers": ["mock"],
            "preferred_provider": "mock",
            "fallback_providers": [],
        }
    )

    assert data["status"] == "HEALTHY"
    assert data["orchestration"]["selected_provider"] == "mock"
    assert data["audit"]["audit_enabled"] is True
