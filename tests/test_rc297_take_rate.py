from app.domains.growth_intelligence.service import GrowthRevenueIntelligenceService


def test_rc297_take_rate():
    s = GrowthRevenueIntelligenceService()
    assert s.calculate_take_rate(revenue=30,gmv=300)["take_rate"]==0.1
