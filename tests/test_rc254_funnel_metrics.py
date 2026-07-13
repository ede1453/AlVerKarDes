from app.domains.user_value.service import UserValueIntelligenceService


def test_rc254_funnel():
    s=UserValueIntelligenceService()
    s.record_journey_event(user_id="u1",event_type="VIEWED")
    s.record_journey_event(user_id="u1",event_type="PURCHASED")
    assert s.calculate_funnel(user_id="u1")["view_to_purchase_rate"]==1.0
