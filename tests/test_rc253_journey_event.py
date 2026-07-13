from app.domains.user_value.service import UserValueIntelligenceService


def test_rc253_journey():
    r=UserValueIntelligenceService().record_journey_event(user_id="u1",event_type="VIEWED")
    assert r["recorded"] is True
