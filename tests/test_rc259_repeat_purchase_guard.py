from app.domains.user_value.service import UserValueIntelligenceService


def test_rc259_repeat_guard():
    s=UserValueIntelligenceService()
    s.record_purchase(user_id="u1",deal_id="d1",product_key="p1",paid_price=700,purchased_at="2026-07-10T00:00:00+00:00")
    r=s.check_repeat_purchase(user_id="u1",product_key="p1",cooldown_days=30,reference_time="2026-07-12T00:00:00+00:00")
    assert r["allowed"] is False
