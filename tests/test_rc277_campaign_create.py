from app.domains.growth_intelligence.service import GrowthRevenueIntelligenceService


def test_rc277_campaign_create():
    s = GrowthRevenueIntelligenceService()
    assert s.create_campaign(campaign_id="c1",name="Launch",budget=1000,starts_at="2026-07-01",ends_at="2026-08-01")["created"] is True
