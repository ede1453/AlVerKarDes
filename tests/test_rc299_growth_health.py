from app.domains.growth_intelligence.service import GrowthRevenueIntelligenceService


def test_rc299_growth_health():
    s = GrowthRevenueIntelligenceService()
    r=s.build_growth_health_report(activation_rate=0.8,retention_rate=0.8,churn_rate=0.1,ltv_cac_ratio=3,revenue_quality_score=100)
    assert r["status"] in {"EXCELLENT","HEALTHY"}