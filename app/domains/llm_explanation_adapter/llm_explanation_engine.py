from app.domains.llm_explanation_adapter.llm_explanation_models import (
    LLMExplanationDraft,
    LLMExplanationInput,
)
from app.domains.llm_explanation_adapter.llm_explanation_prompt_builder import (
    LLMExplanationPromptBuilder,
)


class LLMExplanationAdapterEngine:
    def __init__(self, prompt_builder: LLMExplanationPromptBuilder | None = None):
        self.prompt_builder = prompt_builder or LLMExplanationPromptBuilder()

    def prepare(self, data: LLMExplanationInput) -> LLMExplanationDraft:
        prompt = self.prompt_builder.build(data)
        explanation_text = self._deterministic_explanation(data)

        return LLMExplanationDraft(
            mode="PROMPT_READY",
            language=data.language,
            tone=data.tone,
            explanation_text=explanation_text,
            prompt=prompt,
            prompt_version=prompt.prompt_version,
        )

    def _deterministic_explanation(self, data: LLMExplanationInput) -> str:
        product_name = data.assistant_context.get("product_name") or "this product"

        if data.assistant_decision == "BUY_NOW":
            decision_sentence = f"{product_name} looks like a buy-now opportunity."
        elif data.assistant_decision == "DO_NOT_BUY":
            decision_sentence = f"{product_name} should not be bought from this offer."
        elif data.assistant_decision == "WAIT":
            decision_sentence = f"It is safer to wait before buying {product_name}."
        else:
            decision_sentence = f"It is best to keep watching {product_name}."

        confidence_sentence = f"Confidence is {data.confidence}/100."
        summary_sentence = data.summary

        action_sentence = ""
        if data.next_actions:
            action_sentence = f" Next step: {data.next_actions[0]}"

        return f"{decision_sentence} {summary_sentence} {confidence_sentence}{action_sentence}"
