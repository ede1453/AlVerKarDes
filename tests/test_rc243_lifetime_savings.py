from app.domains.user_value.service import UserValueIntelligenceService


def test_rc243_lifetime_savings():
    s=UserValueIntelligenceService()
    s.record_savings_event(user_id="u1",deal_id="d1",reference_price=1000,paid_price=700)
    s.record_savings_event(user_id="u1",deal_id="d2",reference_price=500,paid_price=400)
    assert s.summarize_lifetime_savings(user_id="u1")["total_savings"]==400
