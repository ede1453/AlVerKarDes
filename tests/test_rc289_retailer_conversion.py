from app.domains.growth_intelligence.service import GrowthRevenueIntelligenceService


def test_rc289_retailer_conversion():
    s = GrowthRevenueIntelligenceService()
    assert s.calculate_retailer_conversion(click_count=100,conversion_count=5)["retailer_conversion_rate"]==0.05
