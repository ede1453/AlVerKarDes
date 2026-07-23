from app.domains.ai_explanation.recommendation_explanation_service import (
    RecommendationExplanationService,
)


def test_rc152_recommendation_explanation():
    result = RecommendationExplanationService().explain(
        recommendation={
            "decision":"BUY",
            "evidence":{
                "observed_discount_pct":25,
                "source_confidence":90,
                "freshness_status":"FRESH",
                "anomaly_detected":False,
            },
        }
    )
    assert result["decision"] == "BUY"
    assert "OBSERVED_DISCOUNT_25" in result["reasons"]
