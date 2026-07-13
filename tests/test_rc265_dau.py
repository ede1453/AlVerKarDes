from app.domains.growth_intelligence.service import GrowthRevenueIntelligenceService


def test_rc265_dau():
    s = GrowthRevenueIntelligenceService()
    r=s.calculate_daily_active_users(user_activity=[{"user_id":"u1","occurred_at":"2026-07-11T12:00:00+00:00"}],reference_time="2026-07-12T00:00:00+00:00")
    assert r["daily_active_users"]==1