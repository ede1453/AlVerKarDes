from app.domains.llm_provider_selection.provider_selection_engine import (
    IntelligentProviderSelectionEngine,
)
from app.domains.llm_provider_selection.provider_selection_models import (
    ProviderSelectionRequest,
)


def test_provider_selection_engine_selects_healthy_mock():
    result = IntelligentProviderSelectionEngine().select(
        ProviderSelectionRequest(
            candidate_providers=["mock", "openai", "local"],
            require_available=True,
        )
    )

    assert result.selected_provider == "mock"
    assert result.fallback_providers == []
    assert any(candidate.provider == "mock" for candidate in result.candidates)


def test_provider_selection_engine_returns_none_when_no_available_provider():
    result = IntelligentProviderSelectionEngine().select(
        ProviderSelectionRequest(
            candidate_providers=["openai", "local"],
            require_available=True,
        )
    )

    assert result.selected_provider is None
    assert result.fallback_providers == []
