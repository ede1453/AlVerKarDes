from app.domains.decision.decision_input_builder import DecisionInputBuilder


def test_decision_input_builder_from_grouped_recommendation():
    payload = DecisionInputBuilder().from_grouped_recommendation(
        selected_group={
            "match_group_id": "group-1",
            "best_offer": {"source": "amazon", "price": 849, "availability": "in_stock", "match_group_score": 100},
            "confidence": {"best_match_group_score": 100},
        },
        recommendation={
            "decision": "BUY",
            "confidence": 70,
            "recommendation_id": "rec-1",
            "evidence": [
                {"type": "PRICE_HISTORY", "confidence": 70, "data": {"current_price": 849, "historical_lowest": 849, "historical_average": 999}},
                {"type": "FRAUD_ANALYSIS", "data": {"risk_level": "LOW"}},
            ],
            "agent_trace": {
                "price_intelligence": {"price_signal": "BUY", "confidence": 70},
                "fraud_agent": {"risk_level": "LOW"},
                "review_analyst": {"review_reliability": "LOW"},
            },
        },
        user_context={"store_trust_score": 90},
    )

    assert payload.price_signal == "BUY"
    assert payload.fraud_risk == "LOW"
    assert payload.match_confidence == 100
    assert payload.current_price == 849
    assert payload.store_trust_score == 90
