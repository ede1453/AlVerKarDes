from app.domains.growth_intelligence.service import GrowthRevenueIntelligenceService


def test_rc266_stickiness():
    s = GrowthRevenueIntelligenceService()
    assert s.calculate_stickiness(daily_active_users=20,monthly_active_users=100)["stickiness"]==0.2
