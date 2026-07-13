from app.domains.user_value.service import UserValueIntelligenceService


def test_rc248_price_alert():
    r=UserValueIntelligenceService().evaluate_price_alert(current_price=700,target_price=750,confidence=85)
    assert r["triggered"] is True
