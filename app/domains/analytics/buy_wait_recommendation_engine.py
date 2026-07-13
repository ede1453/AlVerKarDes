from dataclasses import dataclass


@dataclass
class RecommendationResult:
    recommendation:str
    confidence:int
    reason:str

class BuyWaitRecommendationEngine:
    def recommend(self, *, authenticity_score:int, deal_score:int):
        if authenticity_score>=90 and deal_score>=90:
            return RecommendationResult("BUY_NOW",95,"excellent_authentic_deal")
        if authenticity_score<40:
            return RecommendationResult("AVOID",90,"possible_fake_discount")
        return RecommendationResult("WAIT",70,"better_price_likely")
