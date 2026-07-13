from app.domains.analytics.recommendation_intelligence_engine import (
    RecommendationIntelligenceEngine,
    RecommendationIntelligenceInput,
)


def test_intelligence_engine_returns_buy_now_with_explanations():
    result = RecommendationIntelligenceEngine().evaluate(
        RecommendationIntelligenceInput(
            deal_score=95,
            authenticity_score=96,
            trend_direction="DOWN",
            store_trust_score=90,
            stock_status="in_stock",
        )
    )

    assert result.recommendation == "BUY_NOW"
    assert result.confidence >= 90
    assert "HIGH_DEAL_SCORE" in result.reason_codes
    assert "AUTHENTIC_DISCOUNT" in result.reason_codes
    assert "PRICE_TREND_DOWN" in result.reason_codes
    assert result.explanation


def test_intelligence_engine_avoids_possible_fake_discount():
    result = RecommendationIntelligenceEngine().evaluate(
        RecommendationIntelligenceInput(
            deal_score=98,
            authenticity_score=20,
            trend_direction="DOWN",
            store_trust_score=95,
            stock_status="in_stock",
        )
    )

    assert result.recommendation == "AVOID"
    assert result.confidence == 90
    assert result.reason_codes == ["POSSIBLE_FAKE_DISCOUNT"]


def test_intelligence_engine_returns_watch_for_moderate_signals():
    result = RecommendationIntelligenceEngine().evaluate(
        RecommendationIntelligenceInput(
            deal_score=75,
            authenticity_score=80,
            trend_direction="FLAT",
            store_trust_score=80,
            stock_status="in_stock",
        )
    )

    assert result.recommendation == "WATCH"
    assert "MODERATE_SIGNAL" in result.reason_codes
