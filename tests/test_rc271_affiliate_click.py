from app.domains.growth_intelligence.service import GrowthRevenueIntelligenceService


def test_rc271_affiliate_click():
    s = GrowthRevenueIntelligenceService()
    assert s.record_affiliate_click(user_id="u1",deal_id="d1",retailer_id="r1")["recorded"] is True
