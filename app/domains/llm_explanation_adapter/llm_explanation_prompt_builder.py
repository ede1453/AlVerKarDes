from app.domains.llm_explanation_adapter.llm_explanation_models import (
    LLMExplanationInput,
    LLMExplanationPrompt,
)


class LLMExplanationPromptBuilder:
    SUPPORTED_PROMPT_VERSIONS = {"shopping_v1"}

    def build(self, data: LLMExplanationInput) -> LLMExplanationPrompt:
        prompt_version = self._normalize_prompt_version(data.prompt_version)

        system_prompt = (
            "You are an AI shopping explanation assistant. "
            "Explain the decision clearly without changing the final decision. "
            "Do not invent prices, discounts, sellers, warranties, or facts not present in context."
        )

        guardrails = [
            "Do not change assistant_decision.",
            "Do not provide financial advice.",
            "Do not invent missing product or seller facts.",
            "Mention uncertainty when signals are incomplete.",
            "Keep the explanation concise and user-facing.",
        ]

        user_prompt = self._build_user_prompt(data, prompt_version=prompt_version)

        return LLMExplanationPrompt(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            guardrails=guardrails,
            prompt_version=prompt_version,
            structured_context={
                "assistant_decision": data.assistant_decision,
                "headline": data.headline,
                "summary": data.summary,
                "confidence": data.confidence,
                "risk_level": data.risk_level,
                "opportunity_level": data.opportunity_level,
                "next_actions": list(data.next_actions),
                "reason_codes": list(data.reason_codes),
                "explanation": list(data.explanation),
                "assistant_context": dict(data.assistant_context),
                "language": data.language,
                "tone": data.tone,
                "prompt_version": prompt_version,
            },
        )

    def _normalize_prompt_version(self, prompt_version: str | None) -> str:
        if prompt_version in self.SUPPORTED_PROMPT_VERSIONS:
            return prompt_version
        return "shopping_v1"

    def _build_user_prompt(self, data: LLMExplanationInput, *, prompt_version: str) -> str:
        product_name = data.assistant_context.get("product_name") or "this product"

        return (
            f"Prompt version: {prompt_version}\n"
            f"Write a {data.tone} explanation in {data.language} for the shopping decision.\n"
            f"Product: {product_name}\n"
            f"Decision: {data.assistant_decision}\n"
            f"Headline: {data.headline}\n"
            f"Summary: {data.summary}\n"
            f"Confidence: {data.confidence}\n"
            f"Risk level: {data.risk_level}\n"
            f"Opportunity level: {data.opportunity_level}\n"
            f"Reason codes: {', '.join(data.reason_codes) if data.reason_codes else 'none'}\n"
            f"Next actions: {'; '.join(data.next_actions) if data.next_actions else 'none'}\n"
        )
