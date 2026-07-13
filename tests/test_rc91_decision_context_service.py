from app.domains.decision_context.decision_context_service import DecisionContextService


def test_decision_context_service_returns_serialized_context():
    data = DecisionContextService().build(
        {
            "product_id": "product-1",
            "offer_id": "offer-1",
            "deal_score": 95,
            "authenticity_score": 96,
            "recommendation": "BUY_NOW",
            "recommendation_confidence": 94,
            "final_decision": "BUY_NOW",
            "risk_level": "LOW",
            "opportunity_level": "HIGH",
            "reason_codes": ["HIGH_DEAL_SCORE"],
            "explanation": ["Deal score is high."],
        }
    )

    assert data["context_id"].startswith("decision-context::offer-1::")
    assert data["scores"]["authenticity_score"] == 96
    assert data["decision"]["risk_level"] == "LOW"
    assert data["trace"][0]["stage"] == "context_created"
