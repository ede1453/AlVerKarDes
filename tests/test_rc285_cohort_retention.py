from app.domains.growth_intelligence.service import GrowthRevenueIntelligenceService


def test_rc285_cohort_retention():
    s = GrowthRevenueIntelligenceService()
    s.create_cohort(cohort_id="co1",user_ids=["u1","u2"],started_at="2026-07-01")
    assert s.calculate_cohort_retention(cohort_id="co1",active_user_ids=["u1"])["retention_rate"]==0.5