from app.domains.growth_intelligence.service import GrowthRevenueIntelligenceService


def test_rc286_reactivation():
    s = GrowthRevenueIntelligenceService()
    assert s.calculate_reactivation_rate(inactive_users=100,reactivated_users=10)["reactivation_rate"]==0.1
