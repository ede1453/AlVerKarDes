from app.domains.growth_intelligence.service import GrowthRevenueIntelligenceService


def test_rc298_revenue_quality():
    s = GrowthRevenueIntelligenceService()
    assert s.calculate_revenue_quality(total_revenue=100,disclosed_revenue=100,trust_compliant_revenue=100)["revenue_quality_score"]==100
