from app.domains.user_value.service import UserValueIntelligenceService


def test_rc241_savings_calculation():
    r=UserValueIntelligenceService().calculate_savings(reference_price=1000,paid_price=700,shipping_cost=20)
    assert r["savings_amount"]==280
