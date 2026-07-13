from app.domains.user_value.service import UserValueIntelligenceService


def test_rc256_churn():
    r=UserValueIntelligenceService().calculate_churn_risk(days_since_last_open=60,notifications_ignored=20,false_positive_reports=5,saved_search_count=0)
    assert r["risk_level"]=="HIGH"
