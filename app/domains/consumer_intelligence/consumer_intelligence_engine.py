from dataclasses import dataclass, field


@dataclass
class ConsumerIntelligenceInput:
    deal_score: int
    authenticity_score: int
    recommendation: str
    recommendation_confidence: int
    trend_direction: str | None = None
    store_trust_score: int | None = None
    stock_status: str | None = None
    reason_codes: list[str] = field(default_factory=list)


@dataclass
class ConsumerIntelligenceResult:
    final_decision: str
    confidence: int
    risk_level: str
    opportunity_level: str
    reason_codes: list[str]
    explanation: list[str]


class ConsumerIntelligenceEngine:
    def evaluate(self, data: ConsumerIntelligenceInput) -> ConsumerIntelligenceResult:
        reason_codes = list(data.reason_codes)
        explanation: list[str] = []

        if data.authenticity_score < 40:
            reason_codes.append("HIGH_AUTHENTICITY_RISK")
            explanation.append("Discount authenticity is too low for a safe purchase.")
            return ConsumerIntelligenceResult(
                final_decision="DO_NOT_BUY",
                confidence=max(90, data.recommendation_confidence),
                risk_level="HIGH",
                opportunity_level="LOW",
                reason_codes=self._unique(reason_codes),
                explanation=explanation,
            )

        if data.recommendation == "BUY_NOW" and data.deal_score >= 90 and data.authenticity_score >= 90:
            reason_codes.append("STRONG_BUY_SIGNAL")
            explanation.append("Deal score and authenticity score are both high.")

            if (data.trend_direction or "").upper() == "DOWN":
                reason_codes.append("FAVORABLE_PRICE_TREND")
                explanation.append("Price trend supports the opportunity.")

            if data.store_trust_score is not None and data.store_trust_score >= 85:
                reason_codes.append("TRUSTED_STORE")
                explanation.append("Store trust score is high.")

            if (data.stock_status or "").lower() == "in_stock":
                reason_codes.append("AVAILABLE_NOW")
                explanation.append("Product is currently available.")

            confidence = min(99, max(data.recommendation_confidence, 90) + 3)

            return ConsumerIntelligenceResult(
                final_decision="BUY_NOW",
                confidence=confidence,
                risk_level="LOW",
                opportunity_level="HIGH",
                reason_codes=self._unique(reason_codes),
                explanation=explanation,
            )

        if data.deal_score < 60:
            reason_codes.append("WEAK_DEAL")
            explanation.append("Deal score is weak; waiting is safer.")
            return ConsumerIntelligenceResult(
                final_decision="WAIT",
                confidence=max(70, data.recommendation_confidence),
                risk_level="MEDIUM",
                opportunity_level="LOW",
                reason_codes=self._unique(reason_codes),
                explanation=explanation,
            )

        reason_codes.append("MIXED_SIGNALS")
        explanation.append("Signals are mixed; monitoring the price is recommended.")

        return ConsumerIntelligenceResult(
            final_decision="WATCH",
            confidence=max(70, data.recommendation_confidence),
            risk_level="MEDIUM",
            opportunity_level="MEDIUM",
            reason_codes=self._unique(reason_codes),
            explanation=explanation,
        )

    def _unique(self, values: list[str]) -> list[str]:
        seen = set()
        result = []
        for value in values:
            if value not in seen:
                seen.add(value)
                result.append(value)
        return result
