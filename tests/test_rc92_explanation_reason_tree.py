from app.domains.explainability.explainability_engine import ExplainabilityEngine
from app.domains.explainability.explanation_models import ExplanationInput


def test_reason_tree_contains_weighted_reason_codes():
    result = ExplainabilityEngine().explain(
        ExplanationInput(
            final_decision="BUY_NOW",
            confidence=95,
            reason_codes=["STRONG_BUY_SIGNAL", "FAVORABLE_PRICE_TREND"],
        )
    )

    weights = {item["code"]: item["weight"] for item in result.reason_tree}

    assert weights["STRONG_BUY_SIGNAL"] == 5
    assert weights["FAVORABLE_PRICE_TREND"] == 3
