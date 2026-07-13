from dataclasses import dataclass
from decimal import Decimal


@dataclass
class DiscountQualityResult:
    quality:str
    score:int
    reason:str

class DiscountQualityEngine:
    def evaluate(self,current_price:Decimal,historical_low:Decimal)->DiscountQualityResult:
        if current_price<=historical_low:
            return DiscountQualityResult("EXCELLENT",95,"new_historical_low")
        return DiscountQualityResult("NORMAL",60,"above_historical_low")
