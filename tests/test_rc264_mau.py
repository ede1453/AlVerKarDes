from app.domains.growth_intelligence.service import GrowthRevenueIntelligenceService


def test_rc264_mau():
    s = GrowthRevenueIntelligenceService()
    r=s.calculate_monthly_active_users(user_activity=[{"user_id":"u1","occurred_at":"2026-07-01T00:00:00+00:00"}],reference_time="2026-07-12T00:00:00+00:00")
    assert r["monthly_active_users"]==1