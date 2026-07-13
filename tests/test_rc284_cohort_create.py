from app.domains.growth_intelligence.service import GrowthRevenueIntelligenceService


def test_rc284_cohort_create():
    s = GrowthRevenueIntelligenceService()
    assert s.create_cohort(cohort_id="co1",user_ids=["u1","u2"],started_at="2026-07-01")["created"] is True
