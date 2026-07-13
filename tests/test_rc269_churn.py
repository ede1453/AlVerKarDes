from app.domains.growth_intelligence.service import GrowthRevenueIntelligenceService


def test_rc269_churn():
    s = GrowthRevenueIntelligenceService()
    assert s.calculate_churn_rate(starting_users=100,churned_users=10)["churn_rate"]==0.1
