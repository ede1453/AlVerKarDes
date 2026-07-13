from app.domains.growth_intelligence.service import GrowthRevenueIntelligenceService


def test_rc274_revenue_per_click():
    s = GrowthRevenueIntelligenceService()
    c=s.record_affiliate_click(user_id="u1",deal_id="d1",retailer_id="r1")["click"]
    s.record_affiliate_conversion(click_id=c["click_id"],order_value=1000,commission_value=20)
    assert s.calculate_revenue_per_click()["revenue_per_click"]==20