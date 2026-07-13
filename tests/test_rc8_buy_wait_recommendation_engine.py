from app.domains.analytics.buy_wait_recommendation_engine import BuyWaitRecommendationEngine


def test_buy_now():
    r=BuyWaitRecommendationEngine().recommend(authenticity_score=95,deal_score=96)
    assert r.recommendation=="BUY_NOW"

def test_avoid():
    r=BuyWaitRecommendationEngine().recommend(authenticity_score=20,deal_score=95)
    assert r.recommendation=="AVOID"

def test_wait():
    r=BuyWaitRecommendationEngine().recommend(authenticity_score=70,deal_score=70)
    assert r.recommendation=="WAIT"
