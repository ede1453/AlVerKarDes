from app.domains.observability.metrics_engine import ObservabilityMetricsEngine


def test_observability_metrics_engine_builds_snapshot():
    snapshot = ObservabilityMetricsEngine().snapshot(
        {
            "providers": ["mock", "openai", "local"],
            "preferred_provider": "mock",
            "fallback_providers": [],
            "prompt_version": "shopping_v1",
        }
    )

    assert snapshot.status in {"HEALTHY", "DEGRADED"}
    assert snapshot.orchestration.status == "COMPLETED"
    assert snapshot.orchestration.selected_provider == "mock"
    assert snapshot.audit.audit_enabled is True
    assert any(provider.provider == "mock" for provider in snapshot.providers)
