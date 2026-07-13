from app.domains.analytics.discount_authenticity_engine import DiscountAuthenticityEngine


def test_fake_discount_has_low_authenticity():
    r=DiscountAuthenticityEngine().evaluate(fake_discount_detected=True,quality_score=95)
    assert r.score==10
    assert r.verdict=="FAKE"

def test_real_discount_has_high_authenticity():
    r=DiscountAuthenticityEngine().evaluate(fake_discount_detected=False,quality_score=95)
    assert r.verdict=="AUTHENTIC"