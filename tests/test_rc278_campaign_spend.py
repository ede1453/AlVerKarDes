from app.domains.growth_intelligence.service import GrowthRevenueIntelligenceService


def test_rc278_campaign_spend():
    s = GrowthRevenueIntelligenceService()
    s.create_campaign(campaign_id="c1",name="Launch",budget=100,starts_at="a",ends_at="b")
    r=s.record_campaign_spend(campaign_id="c1",amount=100)
    assert r["campaign"]["status"]=="BUDGET_EXHAUSTED"