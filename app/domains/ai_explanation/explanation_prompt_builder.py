class ExplanationPromptBuilder:
    def build(self, payload: dict):
        language = payload.get("language", "en")
        tone = payload.get("tone", "clear")

        structured_context = {
            "agent_decision": payload.get("agent_decision"),
            "deal_detection": payload.get("deal_detection"),
            "discount_intelligence": payload.get("discount_intelligence"),
            "smart_alert": payload.get("smart_alert"),
            "price_prediction": payload.get("price_prediction"),
            "language": language,
            "tone": tone,
            "prompt_version": payload.get("prompt_version", "shopping_explanation_v1"),
        }

        system_prompt = (
            "You are an AI shopping explanation assistant. Explain the shopping decision clearly. "
            "Do not invent prices, sellers, warranties, stock, or facts not present in context."
        )

        user_prompt = (
            f"Prompt version: {structured_context['prompt_version']}\n"
            f"Language: {language}\n"
            f"Tone: {tone}\n"
            "Explain whether this shopping opportunity is worth acting on using only the structured context.\n"
            f"Structured context: {structured_context}\n"
        )

        return {
            "system_prompt": system_prompt,
            "user_prompt": user_prompt,
            "guardrails": [
                "Do not invent missing marketplace facts.",
                "Mention uncertainty when signals are incomplete.",
                "Do not change the underlying decision.",
                "Do not provide financial advice.",
                "Keep explanation user-facing and concise.",
            ],
            "structured_context": structured_context,
            "prompt_version": structured_context["prompt_version"],
        }
