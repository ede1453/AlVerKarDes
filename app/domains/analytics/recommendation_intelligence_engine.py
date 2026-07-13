from dataclasses import dataclass, field


@dataclass
class RecommendationIntelligenceInput:
    deal_score: int
    authenticity_score: int
    trend_direction: str | None = None
    store_trust_score: int | None = None
    stock_status: str | None = None


@dataclass
class RecommendationIntelligenceResult:
    recommendation: str
    confidence: int
    reason_codes: list[str] = field(default_factory=list)
    explanation: list[str] = field(default_factory=list)


class RecommendationIntelligenceEngine:
    def evaluate(self, data: RecommendationIntelligenceInput) -> RecommendationIntelligenceResult:
        reason_codes: list[str] = []
        explanation: list[str] = []

        if data.authenticity_score < 40:
            reason_codes.append("POSSIBLE_FAKE_DISCOUNT")
            explanation.append("Discount authenticity score is low.")
            return RecommendationIntelligenceResult(
                recommendation="AVOID",
                confidence=90,
                reason_codes=reason_codes,
                explanation=explanation,
            )

        if data.deal_score >= 90:
            reason_codes.append("HIGH_DEAL_SCORE")
            explanation.append("Deal score is high.")

        if data.authenticity_score >= 90:
            reason_codes.append("AUTHENTIC_DISCOUNT")
            explanation.append("Discount authenticity score is high.")

        if (data.trend_direction or "").upper() == "DOWN":
            reason_codes.append("PRICE_TREND_DOWN")
            explanation.append("Price trend is moving down.")

        if data.store_trust_score is not None and data.store_trust_score >= 85:
            reason_codes.append("HIGH_STORE_TRUST")
            explanation.append("Store trust score is high.")

        if (data.stock_status or "").lower() == "in_stock":
            reason_codes.append("IN_STOCK")
            explanation.append("Product is currently in stock.")

        if "HIGH_DEAL_SCORE" in reason_codes and "AUTHENTIC_DISCOUNT" in reason_codes:
            confidence = min(99, 75 + len(reason_codes) * 4)
            return RecommendationIntelligenceResult(
                recommendation="BUY_NOW",
                confidence=confidence,
                reason_codes=reason_codes,
                explanation=explanation,
            )

        if data.deal_score < 60:
            reason_codes.append("WEAK_DEAL_SCORE")
            explanation.append("Deal score is not strong enough.")
            return RecommendationIntelligenceResult(
                recommendation="WAIT",
                confidence=70,
                reason_codes=reason_codes,
                explanation=explanation,
            )

        reason_codes.append("MODERATE_SIGNAL")
        explanation.append("Signals are positive but not strong enough for a buy-now recommendation.")
        return RecommendationIntelligenceResult(
            recommendation="WATCH",
            confidence=72,
            reason_codes=reason_codes,
            explanation=explanation,
        )
