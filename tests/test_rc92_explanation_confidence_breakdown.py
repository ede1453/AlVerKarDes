from app.domains.explainability.explainability_engine import ExplainabilityEngine
from app.domains.explainability.explanation_models import ExplanationInput


def test_confidence_breakdown_levels():
    high = ExplainabilityEngine().explain(
        ExplanationInput(final_decision="BUY_NOW", confidence=95)
    )

    medium = ExplainabilityEngine().explain(
        ExplanationInput(final_decision="WATCH", confidence=75)
    )

    low = ExplainabilityEngine().explain(
        ExplanationInput(final_decision="WAIT", confidence=50)
    )

    assert high.confidence_breakdown["level"] == "HIGH"
    assert medium.confidence_breakdown["level"] == "MEDIUM"
    assert low.confidence_breakdown["level"] == "LOW"
