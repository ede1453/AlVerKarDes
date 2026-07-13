from app.domains.llm_explanation_adapter.llm_explanation_engine import (
    LLMExplanationAdapterEngine,
)
from app.domains.llm_explanation_adapter.llm_explanation_models import LLMExplanationInput


def test_llm_explanation_engine_prepares_prompt_ready_draft():
    draft = LLMExplanationAdapterEngine().prepare(
        LLMExplanationInput(
            assistant_decision="BUY_NOW",
            headline="Buy MacBook Air now",
            summary="The deal looks strong.",
            confidence=94,
            next_actions=["Check final seller terms before purchase."],
            assistant_context={"product_name": "MacBook Air"},
        )
    )

    assert draft.mode == "PROMPT_READY"
    assert "MacBook Air looks like a buy-now opportunity" in draft.explanation_text
    assert draft.prompt.structured_context["confidence"] == 94


def test_llm_explanation_engine_handles_do_not_buy():
    draft = LLMExplanationAdapterEngine().prepare(
        LLMExplanationInput(
            assistant_decision="DO_NOT_BUY",
            headline="Do not buy Unknown Laptop",
            summary="Risk is high.",
            confidence=90,
            assistant_context={"product_name": "Unknown Laptop"},
        )
    )

    assert "should not be bought" in draft.explanation_text
