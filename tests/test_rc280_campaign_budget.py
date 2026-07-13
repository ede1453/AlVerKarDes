from app.domains.growth_intelligence.service import GrowthRevenueIntelligenceService


def test_rc280_campaign_budget():
    s = GrowthRevenueIntelligenceService()
    s.create_campaign(campaign_id="c1",name="Launch",budget=100,starts_at="a",ends_at="b")
    assert s.evaluate_campaign_budget(campaign_id="c1",requested_amount=50)["allowed"] is True