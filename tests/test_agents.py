from app.domains.ai.agents.fraud_agent import FraudAgent, FraudInput
from app.domains.ai.agents.review_analyst_agent import ReviewAnalystAgent, ReviewInput


def test_fraud_agent_high_risk():
    result = FraudAgent().run(
        FraudInput(offer_url="https://fake-shop.xyz/deal", current_price=200, historical_avg_price=1000, store_name=None, store_trust_score=10)
    )
    assert result.risk_level == "HIGH"


def test_review_agent_detects_battery_pattern():
    reviews = [
        "Great performance but battery life is poor.",
        "The battery drains fast.",
        "Good screen.",
        "Excellent keyboard.",
        "Battery could be better.",
        "Fast and reliable.",
    ]
    result = ReviewAnalystAgent().run(ReviewInput(reviews=reviews))
    assert "battery" in result.recurring_complaints
