from app.domains.growth_intelligence.service import GrowthRevenueIntelligenceService


def test_rc279_campaign_roi():
    s = GrowthRevenueIntelligenceService()
    s.create_campaign(campaign_id="c1",name="Launch",budget=100,starts_at="a",ends_at="b")
    s.record_campaign_spend(campaign_id="c1",amount=100)
    assert s.calculate_campaign_roi(campaign_id="c1",attributed_revenue=200)["roi"]==1.0