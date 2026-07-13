from app.domains.user_value.service import UserValueIntelligenceService


def test_rc245_purchase_timing():
    r=UserValueIntelligenceService().evaluate_purchase_timing(current_price=700,historical_prices=[950,1000,1050,980],trend="FALLING")
    assert r["decision"]=="BUY_NOW"
