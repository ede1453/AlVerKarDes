from app.domains.decision_pipeline.ai_decision_pipeline import (
    AIDecisionPipeline,
    AIDecisionPipelineInput,
)


def test_ai_decision_pipeline_returns_buy_now():
    result = AIDecisionPipeline().run(
        AIDecisionPipelineInput(
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

    assert result.pipeline_status == "PASSED"
    assert result.final_decision == "BUY_NOW"
    assert result.risk_level == "LOW"
    assert result.opportunity_level == "HIGH"
    assert len(result.stages) == 3


def test_ai_decision_pipeline_returns_do_not_buy_for_high_risk():
    result = AIDecisionPipeline().run(
        AIDecisionPipelineInput(
            deal_score=98,
            authenticity_score=20,
            recommendation="AVOID",
            recommendation_confidence=90,
        )
    )

    assert result.pipeline_status == "PASSED"
    assert result.final_decision == "DO_NOT_BUY"
    assert result.risk_level == "HIGH"
