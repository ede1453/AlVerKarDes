from app.domains.user_value.service import UserValueIntelligenceService


def test_rc250_watch_expiry():
    s=UserValueIntelligenceService()
    s.create_watch_entry(user_id="u1",product_key="p1",target_price=700,expires_at="2026-07-01T00:00:00+00:00")
    r=s.expire_watch_entries(reference_time="2026-07-12T00:00:00+00:00")
    assert r["expired_count"]==1
