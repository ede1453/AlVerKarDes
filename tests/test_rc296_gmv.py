from app.domains.growth_intelligence.service import GrowthRevenueIntelligenceService


def test_rc296_gmv():
    s = GrowthRevenueIntelligenceService()
    assert s.calculate_gross_merchandise_value(order_values=[100,200])["gmv"]==300
