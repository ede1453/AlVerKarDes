from decimal import Decimal

from app.domains.analytics.fake_discount_detector import FakeDiscountDetector


def test_detects_temporary_price_inflation():
    r=FakeDiscountDetector().evaluate(
        previous_price=Decimal("699"),
        peak_price=Decimal("999"),
        current_price=Decimal("699"),
    )
    assert r.is_fake_discount is True
    assert r.reason=="temporary_price_inflation_detected"
