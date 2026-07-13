from app.domains.growth_intelligence.service import GrowthRevenueIntelligenceService


def test_rc295_north_star():
    s = GrowthRevenueIntelligenceService()
    assert s.calculate_north_star_metric(qualified_deal_views=10,accepted_recommendations=10,purchases=10)["north_star_value"]==10
