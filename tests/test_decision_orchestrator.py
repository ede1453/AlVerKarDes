from app.domains.recommendations.decision_orchestrator import DecisionInput, DecisionOrchestrator


def test_fraud_overrides_buy_signal():
    result = DecisionOrchestrator().decide(DecisionInput(product_confidence=95, price_signal="BUY", price_confidence=90, review_reliability="HIGH", fraud_risk_level="HIGH", fraud_score=90))
    assert result.decision == "DO_NOT_BUY"


def test_low_product_confidence_returns_insufficient_data():
    result = DecisionOrchestrator().decide(DecisionInput(product_confidence=30, price_signal="BUY", price_confidence=90, fraud_risk_level="LOW", fraud_score=0))
    assert result.decision == "INSUFFICIENT_DATA"
