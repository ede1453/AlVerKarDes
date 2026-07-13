from app.domains.ai_shopping_assistant.assistant_models import (
    ShoppingAssistantAdvice,
    ShoppingAssistantInput,
)


class AIShoppingAssistantEngine:
    def advise(self, data: ShoppingAssistantInput) -> ShoppingAssistantAdvice:
        effective_decision = data.personalized_decision or data.final_decision
        effective_confidence = data.personalized_confidence or data.confidence

        assistant_decision = self._assistant_decision(
            decision=effective_decision,
            confidence=effective_confidence,
            risk_level=data.risk_level,
            trust_score=data.trust_score,
        )

        headline = self._headline(assistant_decision, data.product_name)
        summary = self._summary(assistant_decision, data)
        next_actions = self._next_actions(assistant_decision, data)

        reason_codes = self._unique(
            list(data.reason_codes)
            + list(data.personalization_reasons)
            + self._assistant_reason_codes(assistant_decision, data)
        )

        explanation = list(data.explanation)
        if data.personalized_decision is not None:
            explanation.append("The base decision was adjusted using user-specific preference signals.")
        if data.trust_score is not None:
            explanation.append("Trust intelligence was included in the assistant decision.")

        return ShoppingAssistantAdvice(
            assistant_decision=assistant_decision,
            headline=headline,
            summary=summary,
            confidence=effective_confidence,
            risk_level=data.risk_level,
            opportunity_level=data.opportunity_level,
            next_actions=next_actions,
            reason_codes=reason_codes,
            explanation=explanation,
            assistant_context={
                "user_id": data.user_id,
                "query": data.query,
                "product_name": data.product_name,
                "product_brand": data.product_brand,
                "product_category": data.product_category,
                "current_price": data.current_price,
                "currency": data.currency,
                "base_decision": data.final_decision,
                "personalized_decision": data.personalized_decision,
                "trust_score": data.trust_score,
                "community_score": data.community_score,
                "metadata": data.metadata,
            },
        )

    def _assistant_decision(
        self,
        *,
        decision: str,
        confidence: int,
        risk_level: str | None,
        trust_score: int | None,
    ) -> str:
        if risk_level == "HIGH":
            return "DO_NOT_BUY"

        if trust_score is not None and trust_score < 40 and decision == "BUY_NOW":
            return "WATCH"

        if decision in {"AVOID", "DO_NOT_BUY"}:
            return "DO_NOT_BUY"

        if decision == "BUY_NOW" and confidence >= 85:
            return "BUY_NOW"

        if decision == "WAIT":
            return "WAIT"

        return "WATCH"

    def _headline(self, assistant_decision: str, product_name: str | None) -> str:
        subject = product_name or "this product"

        mapping = {
            "BUY_NOW": f"Buy {subject} now",
            "WATCH": f"Watch {subject}",
            "WAIT": f"Wait before buying {subject}",
            "DO_NOT_BUY": f"Do not buy {subject}",
        }

        return mapping.get(assistant_decision, f"Review {subject}")

    def _summary(self, assistant_decision: str, data: ShoppingAssistantInput) -> str:
        if assistant_decision == "BUY_NOW":
            return "The combined decision, personalization, and trust signals support buying now."
        if assistant_decision == "DO_NOT_BUY":
            return "Risk or trust signals are too weak for a safe purchase."
        if assistant_decision == "WAIT":
            return "The current deal is not strong enough; waiting is safer."
        return "Signals are mixed; monitoring this product is the safest next step."

    def _next_actions(self, assistant_decision: str, data: ShoppingAssistantInput) -> list[str]:
        if assistant_decision == "BUY_NOW":
            return [
                "Check final seller terms before purchase.",
                "Confirm warranty, return policy, and delivery cost.",
                "Buy only if the checkout price matches the detected offer.",
            ]

        if assistant_decision == "DO_NOT_BUY":
            return [
                "Avoid purchasing from this offer.",
                "Look for a higher-trust seller.",
                "Wait for stronger authenticity and trust signals.",
            ]

        if assistant_decision == "WAIT":
            return [
                "Set a price alert.",
                "Re-check the product after the next price update.",
                "Compare with trusted alternative stores.",
            ]

        return [
            "Track the product.",
            "Set a target price alert.",
            "Review again when price, trust, or stock signals change.",
        ]

    def _assistant_reason_codes(self, assistant_decision: str, data: ShoppingAssistantInput) -> list[str]:
        if assistant_decision == "BUY_NOW":
            return ["ASSISTANT_BUY_SIGNAL"]
        if assistant_decision == "DO_NOT_BUY":
            return ["ASSISTANT_RISK_BLOCK"]
        if assistant_decision == "WAIT":
            return ["ASSISTANT_WAIT_SIGNAL"]
        return ["ASSISTANT_WATCH_SIGNAL"]

    def _unique(self, values: list[str]) -> list[str]:
        seen = set()
        result = []
        for value in values:
            if value not in seen:
                seen.add(value)
                result.append(value)
        return result
