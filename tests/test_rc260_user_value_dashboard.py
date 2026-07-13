from app.domains.user_value.service import UserValueIntelligenceService


def test_rc260_dashboard():
    s=UserValueIntelligenceService()
    s.record_savings_event(user_id="u1",deal_id="d1",reference_price=1000,paid_price=700)
    r=s.build_user_value_dashboard(user_id="u1",recommendation_count=10,accepted_count=5,purchase_count=2)
    assert r["total_savings"]==300
    assert r["acceptance_rate"]==0.5
