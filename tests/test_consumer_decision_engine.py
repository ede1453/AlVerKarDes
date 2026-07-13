from app.domains.decision.consumer_decision_engine import ConsumerDecisionEngine, ConsumerDecisionInput


def test_decision_engine_buy_now():
    result = ConsumerDecisionEngine().decide(
        ConsumerDecisionInput(
            price_signal="BUY",
            price_confidence=90,
            fake_discount_risk="LOW",
            fraud_risk="LOW",
            match_confidence=95,
            availability="in_stock",
            store_trust_score=90,
            current_price=849,
            historical_lowest=849,
            historical_average=999,
        )
    )

    assert result.decision == "BUY_NOW"
    assert result.score >= 75
    assert result.confidence >= 85
    assert result.reasons


def test_decision_engine_avoid_fake_discount():
    result = ConsumerDecisionEngine().decide(
        ConsumerDecisionInput(
            price_signal="BUY",
            price_confidence=80,
            fake_discount_risk="HIGH",
            fraud_risk="LOW",
            match_confidence=95,
            availability="in_stock",
            store_trust_score=90,
        )
    )

    assert result.decision == "AVOID"
    assert "Possible fake discount pattern detected." in result.risks


def test_decision_engine_wait_when_price_signal_wait():
    result = ConsumerDecisionEngine().decide(
        ConsumerDecisionInput(
            price_signal="WAIT",
            price_confidence=80,
            fake_discount_risk="LOW",
            fraud_risk="LOW",
            match_confidence=90,
            availability="in_stock",
            store_trust_score=80,
        )
    )

    assert result.decision in {"WAIT", "AVOID"}
    assert result.score < 75


def test_decision_engine_insufficient_data():
    result = ConsumerDecisionEngine().decide(
        ConsumerDecisionInput(
            price_signal="INSUFFICIENT_HISTORY",
            price_confidence=20,
            fake_discount_risk="UNKNOWN",
            fraud_risk="UNKNOWN",
            match_confidence=40,
            availability=None,
            store_trust_score=80,
        )
    )

    assert result.decision == "INSUFFICIENT_DATA"
