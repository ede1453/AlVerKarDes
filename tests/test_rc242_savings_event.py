from app.domains.user_value.service import UserValueIntelligenceService


def test_rc242_savings_event():
    r=UserValueIntelligenceService().record_savings_event(user_id="u1",deal_id="d1",reference_price=1000,paid_price=700)
    assert r["recorded"] is True
