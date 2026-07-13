from app.domains.growth_intelligence.service import GrowthRevenueIntelligenceService


def test_rc261_cac():
    s = GrowthRevenueIntelligenceService()
    r=s.calculate_customer_acquisition_cost(marketing_spend=1000,acquired_users=100)
    assert r["cac"]==10