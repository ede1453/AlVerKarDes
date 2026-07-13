from app.domains.decision_pipeline.ai_decision_pipeline_service import (
    AIDecisionPipelineService,
)


def test_ai_decision_pipeline_service_returns_serialized_result():
    data = AIDecisionPipelineService().run(
        {
            "deal_score": 95,
            "authenticity_score": 96,
            "recommendation": "BUY_NOW",
            "recommendation_confidence": 94,
            "trend_direction": "DOWN",
            "store_trust_score": 90,
            "stock_status": "in_stock",
            "reason_codes": ["HIGH_DEAL_SCORE", "AUTHENTIC_DISCOUNT"],
        }
    )

    assert data["pipeline_status"] == "PASSED"
    assert data["final_decision"] == "BUY_NOW"
    assert data["stages"][0]["name"] == "input_validation"
