from app.domains.consumer_intelligence.consumer_intelligence_engine import (
    ConsumerIntelligenceEngine,
    ConsumerIntelligenceInput,
)


def test_consumer_intelligence_returns_buy_now_for_strong_signal():
    result = ConsumerIntelligenceEngine().evaluate(
        ConsumerIntelligenceInput(
            deal_score=95,
            authenticity_score=96,
            recommendation="BUY_NOW",
            recommendation_confidence=94,
            trend_direction="DOWN",
            store_trust_score=90,
            stock_status="in_stock",
            reason_codes=["HIGH_DEAL_SCORE", "AUTHENTIC_DISCOUNT"],
        )
    )

    assert result.final_decision == "BUY_NOW"
    assert result.risk_level == "LOW"
    assert result.opportunity_level == "HIGH"
    assert "STRONG_BUY_SIGNAL" in result.reason_codes


def test_consumer_intelligence_returns_do_not_buy_for_fake_discount_risk():
    result = ConsumerIntelligenceEngine().evaluate(
        ConsumerIntelligenceInput(
            deal_score=98,
            authenticity_score=20,
            recommendation="AVOID",
            recommendation_confidence=90,
        )
    )

    assert result.final_decision == "DO_NOT_BUY"
    assert result.risk_level == "HIGH"
    assert "HIGH_AUTHENTICITY_RISK" in result.reason_codes


def test_consumer_intelligence_returns_watch_for_mixed_signals():
    result = ConsumerIntelligenceEngine().evaluate(
        ConsumerIntelligenceInput(
            deal_score=75,
            authenticity_score=80,
            recommendation="WATCH",
            recommendation_confidence=72,
        )
    )

    assert result.final_decision == "WATCH"
    assert result.risk_level == "MEDIUM"
    assert "MIXED_SIGNALS" in result.reason_codes
