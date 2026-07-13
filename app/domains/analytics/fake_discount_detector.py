from dataclasses import dataclass
from decimal import Decimal


@dataclass
class FakeDiscountResult:
    is_fake_discount: bool
    confidence: int
    reason: str

class FakeDiscountDetector:
    def evaluate(self, previous_price: Decimal, peak_price: Decimal, current_price: Decimal)->FakeDiscountResult:
        if peak_price > previous_price and current_price == previous_price:
            return FakeDiscountResult(True,90,"temporary_price_inflation_detected")
        return FakeDiscountResult(False,80,"no_artificial_pattern_detected")
