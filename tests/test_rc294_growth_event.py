from app.domains.growth_intelligence.service import GrowthRevenueIntelligenceService


def test_rc294_growth_event():
    s = GrowthRevenueIntelligenceService()
    assert s.record_growth_event(user_id="u1",event_type="activated")["recorded"] is True
