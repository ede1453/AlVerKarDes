from dataclasses import dataclass

from app.domains.analytics.recommendation_service import RecommendationService


@dataclass
class RecommendationVerticalSliceResult:
    deal_score: int
    authenticity_score: int
    recommendation: str
    confidence: int
    reason: str
    source: str = "recommendation_vertical_slice"


class RecommendationVerticalSlice:
    def __init__(self, recommendation_service: RecommendationService | None = None):
        self.recommendation_service = recommendation_service or RecommendationService()

    def evaluate(self, *, deal_score: int, authenticity_score: int) -> RecommendationVerticalSliceResult:
        summary = self.recommendation_service.build(
            deal_score=deal_score,
            authenticity_score=authenticity_score,
        )

        return RecommendationVerticalSliceResult(
            deal_score=summary.deal_score,
            authenticity_score=summary.authenticity_score,
            recommendation=summary.recommendation,
            confidence=summary.confidence,
            reason=summary.reason,
        )
