from app.domains.llm_explanation_adapter.llm_explanation_service import (
    LLMExplanationAdapterService,
)


def test_llm_explanation_service_serializes_draft():
    data = LLMExplanationAdapterService().prepare(
        {
            "assistant_decision": "WATCH",
            "headline": "Watch this product",
            "summary": "Signals are mixed.",
            "confidence": 72,
            "assistant_context": {"product_name": "Phone"},
        }
    )

    assert data["mode"] == "PROMPT_READY"
    assert data["prompt"]["structured_context"]["assistant_decision"] == "WATCH"
    assert "Phone" in data["explanation_text"]
