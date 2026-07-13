from app.domains.user_value.service import UserValueIntelligenceService


def test_rc247_alternatives():
    r=UserValueIntelligenceService().rank_alternatives(candidates=[{"id":"a","price":700,"confidence":90,"observed_discount_pct":20}],maximum_price=800,minimum_confidence=70)
    assert r["alternative_count"]==1
