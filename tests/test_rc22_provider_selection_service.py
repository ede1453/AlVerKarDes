from app.domains.llm_provider_selection.provider_selection_service import (
    ProviderSelectionService,
)


def test_provider_selection_service_serializes_result():
    data = ProviderSelectionService().select(
        {
            "candidate_providers": ["mock", "openai"],
            "require_available": True,
        }
    )

    assert data["selected_provider"] == "mock"
    assert data["strategy"] == "health_score_latency_success_rate"
    assert data["candidates"]
