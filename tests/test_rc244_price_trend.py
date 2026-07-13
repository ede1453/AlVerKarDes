from app.domains.user_value.service import UserValueIntelligenceService


def test_rc244_price_trend():
    assert UserValueIntelligenceService().analyze_price_trend(prices=[1000,900,800])["trend"]=="FALLING"
