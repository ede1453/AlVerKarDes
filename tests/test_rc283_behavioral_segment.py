from app.domains.growth_intelligence.service import GrowthRevenueIntelligenceService


def test_rc283_behavioral_segment():
    s = GrowthRevenueIntelligenceService()
    assert s.build_behavioral_segment(user_id="u1",purchase_count=5,alert_count=0,open_rate=0)["behavioral_segment"]=="POWER_BUYER"
