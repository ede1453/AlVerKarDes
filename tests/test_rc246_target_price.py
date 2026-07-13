from app.domains.user_value.service import UserValueIntelligenceService


def test_rc246_target_price():
    r=UserValueIntelligenceService().calculate_target_price(historical_prices=[900,1000,1100],desired_discount_pct=20)
    assert r["target_price"]==800
