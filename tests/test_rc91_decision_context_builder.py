from app.domains.decision_context.decision_context_builder import (
    DecisionContextBuilder,
    DecisionContextInput,
)


def test_decision_context_builder_builds_context():
    context = DecisionContextBuilder().build(
        DecisionContextInput(
            product_id="product-1",
            offer_id="offer-1",
            deal_score=95,
            authenticity_score=96,
            recommendation="BUY_NOW",
            recommendation_confidence=94,
            final_decision="BUY_NOW",
            risk_level="LOW",
            opportunity_level="HIGH",
            reason_codes=["HIGH_DEAL_SCORE"],
            explanation=["Deal score is high."],
        )
    )

    assert context.context_id.startswith("decision-context::offer-1::")
    assert context.market["country"] == "DE"
    assert context.scores["deal_score"] == 95
    assert context.decision["final_decision"] == "BUY_NOW"
    assert len(context.trace) == 3
