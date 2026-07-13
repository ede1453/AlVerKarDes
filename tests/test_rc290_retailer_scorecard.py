from app.domains.growth_intelligence.service import GrowthRevenueIntelligenceService


def test_rc290_retailer_scorecard():
    s = GrowthRevenueIntelligenceService()
    r=s.build_retailer_scorecard(retailer_id="r1",quality_score=90,conversion_rate=0.1,average_discount_pct=20,trust_score=90)
    assert r["score"]>50