from app.domains.growth_intelligence.service import GrowthRevenueIntelligenceService


def test_rc287_retailer_snapshot():
    s = GrowthRevenueIntelligenceService()
    assert s.record_retailer_snapshot(retailer_id="r1",offer_count=10,valid_offer_count=9,average_discount_pct=20,conversion_count=2)["recorded"] is True
