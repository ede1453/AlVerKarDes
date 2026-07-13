from app.domains.growth_intelligence.service import GrowthRevenueIntelligenceService


def test_rc268_retention():
    s = GrowthRevenueIntelligenceService()
    assert s.calculate_retention_rate(cohort_size=100,retained_users=60)["retention_rate"]==0.6
