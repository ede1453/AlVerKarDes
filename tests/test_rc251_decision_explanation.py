from app.domains.user_value.service import UserValueIntelligenceService


def test_rc251_explain():
    r=UserValueIntelligenceService().explain_decision(decision="BUY",confidence=90,evidence={"observed_discount_pct":30,"source_confidence":90})
    assert r["explainable"] is True
