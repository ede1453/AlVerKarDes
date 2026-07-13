from app.domains.user_value.service import UserValueIntelligenceService


def test_rc257_retention():
    r=UserValueIntelligenceService().recommend_retention_action(churn_risk_score=80,recent_false_positive=True,has_saved_searches=False)
    assert r["action"]=="TRUST_RECOVERY_MESSAGE"
