from app.domains.explainability.explanation_service import ExplanationService


def test_explanation_service_serializes_result():
    data = ExplanationService().explain(
        {
            "final_decision": "BUY_NOW",
            "confidence": 94,
            "risk_level": "LOW",
            "opportunity_level": "HIGH",
            "reason_codes": ["STRONG_BUY_SIGNAL"],
            "scores": {"deal_score": 95},
        }
    )

    assert data["headline"] == "Buy now"
    assert data["confidence_breakdown"]["overall"] == 94
    assert data["llm_prompt_context"]["final_decision"] == "BUY_NOW"
