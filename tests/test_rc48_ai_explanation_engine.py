from app.domains.ai_explanation.explanation_engine import AIExplanationEngine


def test_ai_explanation_engine_explains_buy_opportunity():
    result = AIExplanationEngine().explain(
        agent_decision={"decision": "BUY_NOW"},
        deal_detection={"deal_level": "EXCELLENT_DEAL"},
        discount_intelligence={"discount_quality": "EXCELLENT_REAL_DISCOUNT", "fake_discount_risk": "LOW"},
        smart_alert={"alert_level": "URGENT"},
        price_prediction={"recommendation_hint": "BUY_SOON"},
    )

    assert result["headline"] == "This looks like a strong buy opportunity"
    assert "Agent decision: BUY_NOW." in result["bullet_points"]
    assert result["next_actions"]


def test_ai_explanation_engine_mentions_fake_discount_risk():
    result = AIExplanationEngine().explain(
        discount_intelligence={"discount_quality": "WEAK_DISCOUNT", "fake_discount_risk": "HIGH"},
    )

    assert result["risk_notes"]
    assert "Fake discount risk is high" in result["risk_notes"][0]
