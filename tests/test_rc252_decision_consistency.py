from app.domains.user_value.service import UserValueIntelligenceService


def test_rc252_consistency():
    r=UserValueIntelligenceService().check_decision_consistency(decision="BUY",confidence=90,anomaly_detected=False,source_confidence=90)
    assert r["consistent"] is True
