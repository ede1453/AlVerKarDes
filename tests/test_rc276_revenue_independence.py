from app.domains.growth_intelligence.service import GrowthRevenueIntelligenceService


def test_rc276_revenue_independence():
    s = GrowthRevenueIntelligenceService()
    assert s.evaluate_revenue_independence(recommendation_score=90,commission_rate=5,ranking_changed=False)["compliant"] is True
