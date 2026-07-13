from app.domains.llm_explanation_adapter.llm_explanation_models import LLMExplanationInput
from app.domains.llm_explanation_adapter.llm_explanation_prompt_builder import (
    LLMExplanationPromptBuilder,
)


def test_llm_explanation_prompt_builder_keeps_decision_guardrail():
    prompt = LLMExplanationPromptBuilder().build(
        LLMExplanationInput(
            assistant_decision="BUY_NOW",
            headline="Buy MacBook Air now",
            summary="The deal looks strong.",
            confidence=94,
            reason_codes=["ASSISTANT_BUY_SIGNAL"],
            assistant_context={"product_name": "MacBook Air"},
        )
    )

    assert "Do not change assistant_decision." in prompt.guardrails
    assert prompt.structured_context["assistant_decision"] == "BUY_NOW"
    assert "MacBook Air" in prompt.user_prompt
