from app.domains.cache.cache_key_builder import CacheKeyBuilder
from app.domains.cache.cache_service import CacheService
from app.domains.llm_orchestration.orchestration_service import LLMOrchestrationService


def test_cache_vertical_slice_wraps_orchestration_result():
    service = CacheService()
    key = CacheKeyBuilder().build(
        namespace="orchestration",
        payload={"provider": "mock", "decision": "BUY_NOW", "product": "MacBook Air"},
    )

    def run_orchestration():
        return LLMOrchestrationService().run(
            {
                "preferred_provider": "mock",
                "fallback_providers": [],
                "system_prompt": "Explain safely.",
                "user_prompt": "Explain BUY_NOW.",
                "guardrails": ["Do not change assistant_decision."],
                "structured_context": {
                    "assistant_decision": "BUY_NOW",
                    "assistant_context": {"product_name": "MacBook Air"},
                    "prompt_version": "shopping_v1",
                },
                "prompt_version": "shopping_v1",
            }
        )

    first = service.get_or_set(key=key, value_factory=run_orchestration, ttl_seconds=300)
    second = service.get_or_set(key=key, value_factory=run_orchestration, ttl_seconds=300)

    assert first["cache_hit"] is False
    assert second["cache_hit"] is True
    assert second["value"]["status"] == "COMPLETED"
