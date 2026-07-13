from app.domains.user_value.service import UserValueIntelligenceService


def test_rc258_purchase():
    r=UserValueIntelligenceService().record_purchase(user_id="u1",deal_id="d1",product_key="p1",paid_price=700)
    assert r["recorded"] is True
