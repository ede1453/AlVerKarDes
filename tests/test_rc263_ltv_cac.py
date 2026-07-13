from app.domains.growth_intelligence.service import GrowthRevenueIntelligenceService


def test_rc263_ltv_cac():
    s = GrowthRevenueIntelligenceService()
    r=s.calculate_ltv_cac_ratio(ltv=300,cac=100)
    assert r["status"]=="HEALTHY"