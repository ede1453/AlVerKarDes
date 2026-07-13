from app.domains.analytics.recommendation_service import RecommendationService


def test_buy_summary():
    r=RecommendationService().build(deal_score=95,authenticity_score=96)
    assert r.recommendation=="BUY_NOW"

def test_wait_summary():
    r=RecommendationService().build(deal_score=70,authenticity_score=70)
    assert r.recommendation=="WAIT"

def test_avoid_summary():
    r=RecommendationService().build(deal_score=99,authenticity_score=10)
    assert r.recommendation=="AVOID"