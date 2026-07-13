from app.domains.growth_intelligence.service import GrowthRevenueIntelligenceService


def test_rc267_activation():
    s = GrowthRevenueIntelligenceService()
    assert s.calculate_activation_rate(registered_users=100,activated_users=40)["activation_rate"]==0.4
