from app.domains.growth_intelligence.service import GrowthRevenueIntelligenceService


def test_rc300_executive_dashboard():
    s = GrowthRevenueIntelligenceService()
    r=s.build_executive_dashboard(mau=100,dau=20,activation_rate=0.5,retention_rate=0.6,churn_rate=0.1,gmv=1000,revenue=100,trust_score=90,growth_health_score=80)
    assert r["take_rate"]==0.1