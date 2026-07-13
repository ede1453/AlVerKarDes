from app.domains.explainability.explainability_engine import ExplainabilityEngine
from app.domains.explainability.explanation_models import ExplanationInput


def test_explainability_engine_generates_buy_now_explanation():
    result = ExplainabilityEngine().explain(
        ExplanationInput(
            final_decision="BUY_NOW",
            confidence=94,
            risk_level="LOW",
            opportunity_level="HIGH",
            reason_codes=["STRONG_BUY_SIGNAL", "TRUSTED_STORE"],
            explanation=["Deal score and authenticity score are both high."],
            scores={"deal_score": 95, "authenticity_score": 96},
            market={"country": "DE", "currency": "EUR"},
        )
    )

    assert result.headline == "Buy now"
    assert result.confidence_breakdown["level"] == "HIGH"
    assert result.opportunity_breakdown["is_high_opportunity"] is True
    assert result.reason_tree


def test_explainability_engine_generates_do_not_buy_explanation():
    result = ExplainabilityEngine().explain(
        ExplanationInput(
            final_decision="DO_NOT_BUY",
            confidence=90,
            risk_level="HIGH",
            opportunity_level="LOW",
            reason_codes=["HIGH_AUTHENTICITY_RISK"],
        )
    )

    assert result.headline == "Do not buy"
    assert result.risk_breakdown["is_high_risk"] is True
