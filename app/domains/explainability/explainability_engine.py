from app.domains.explainability.explanation_models import (
    ExplanationInput,
    ExplanationResult,
)


class ExplainabilityEngine:
    def explain(self, data: ExplanationInput) -> ExplanationResult:
        headline = self._headline(data.final_decision)
        summary = self._summary(data)

        return ExplanationResult(
            headline=headline,
            summary=summary,
            reason_tree=self._reason_tree(data),
            confidence_breakdown=self._confidence_breakdown(data),
            risk_breakdown=self._risk_breakdown(data),
            opportunity_breakdown=self._opportunity_breakdown(data),
            llm_prompt_context=self._llm_prompt_context(data, headline, summary),
        )

    def _headline(self, final_decision: str) -> str:
        mapping = {
            "BUY_NOW": "Buy now",
            "WATCH": "Watch this deal",
            "WAIT": "Wait for a better price",
            "DO_NOT_BUY": "Do not buy",
            "AVOID": "Avoid this deal",
        }
        return mapping.get(final_decision, "Review this deal")

    def _summary(self, data: ExplanationInput) -> str:
        if data.final_decision == "BUY_NOW":
            return "Signals are strong enough to recommend buying now."
        if data.final_decision in {"DO_NOT_BUY", "AVOID"}:
            return "Risk signals are too high for a safe purchase."
        if data.final_decision == "WAIT":
            return "The deal is not strong enough yet; waiting is safer."
        return "Signals are mixed; continued monitoring is recommended."

    def _reason_tree(self, data: ExplanationInput) -> list[dict]:
        tree = []

        for code in data.reason_codes:
            tree.append(
                {
                    "code": code,
                    "weight": self._reason_weight(code),
                    "message": self._reason_message(code),
                }
            )

        for item in data.explanation:
            tree.append(
                {
                    "code": "NARRATIVE_EXPLANATION",
                    "weight": 1,
                    "message": item,
                }
            )

        return tree

    def _reason_weight(self, code: str) -> int:
        high_weight = {
            "STRONG_BUY_SIGNAL",
            "HIGH_AUTHENTICITY_RISK",
            "HIGH_DEAL_SCORE",
            "AUTHENTIC_DISCOUNT",
        }

        if code in high_weight:
            return 5

        if code in {"FAVORABLE_PRICE_TREND", "TRUSTED_STORE", "AVAILABLE_NOW"}:
            return 3

        return 2

    def _reason_message(self, code: str) -> str:
        messages = {
            "STRONG_BUY_SIGNAL": "Deal and authenticity signals are both strong.",
            "HIGH_AUTHENTICITY_RISK": "Discount authenticity risk is high.",
            "HIGH_DEAL_SCORE": "Deal score is high.",
            "AUTHENTIC_DISCOUNT": "Discount appears authentic.",
            "FAVORABLE_PRICE_TREND": "Price trend supports the decision.",
            "TRUSTED_STORE": "Store trust signal is positive.",
            "AVAILABLE_NOW": "Product is available now.",
            "MIXED_SIGNALS": "Signals are mixed.",
            "WEAK_DEAL": "Deal score is weak.",
        }
        return messages.get(code, code.lower().replace("_", " "))

    def _confidence_breakdown(self, data: ExplanationInput) -> dict:
        return {
            "overall": data.confidence,
            "level": self._level(data.confidence),
            "drivers": list(data.reason_codes),
        }

    def _risk_breakdown(self, data: ExplanationInput) -> dict:
        return {
            "level": data.risk_level,
            "is_high_risk": data.risk_level == "HIGH",
            "signals": [code for code in data.reason_codes if "RISK" in code or "FAKE" in code],
        }

    def _opportunity_breakdown(self, data: ExplanationInput) -> dict:
        return {
            "level": data.opportunity_level,
            "is_high_opportunity": data.opportunity_level == "HIGH",
            "signals": [
                code
                for code in data.reason_codes
                if code in {"STRONG_BUY_SIGNAL", "HIGH_DEAL_SCORE", "FAVORABLE_PRICE_TREND"}
            ],
        }

    def _llm_prompt_context(self, data: ExplanationInput, headline: str, summary: str) -> dict:
        return {
            "headline": headline,
            "summary": summary,
            "final_decision": data.final_decision,
            "confidence": data.confidence,
            "risk_level": data.risk_level,
            "opportunity_level": data.opportunity_level,
            "reason_codes": list(data.reason_codes),
            "scores": dict(data.scores),
            "market": dict(data.market),
        }

    def _level(self, score: int) -> str:
        if score >= 90:
            return "HIGH"
        if score >= 70:
            return "MEDIUM"
        return "LOW"
