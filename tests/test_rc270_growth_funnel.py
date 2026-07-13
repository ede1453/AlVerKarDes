from app.domains.growth_intelligence.service import GrowthRevenueIntelligenceService


def test_rc270_growth_funnel():
    s = GrowthRevenueIntelligenceService()
    r=s.build_growth_funnel(visitors=1000,registrations=200,activations=100,alerts_created=50,purchases=10)
    assert r["alert_to_purchase"]==0.2