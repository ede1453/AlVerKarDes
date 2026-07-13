from decimal import Decimal

from app.domains.analytics.discount_quality_engine import DiscountQualityEngine


def test_new_historical_low():
    r=DiscountQualityEngine().evaluate(Decimal("799"),Decimal("799"))
    assert r.quality=="EXCELLENT"
