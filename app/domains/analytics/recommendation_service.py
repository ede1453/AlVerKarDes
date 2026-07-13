from dataclasses import dataclass


@dataclass
class RecommendationSummary:
    deal_score:int
    authenticity_score:int
    recommendation:str
    confidence:int
    reason:str

class RecommendationService:
    def build(self, *, deal_score:int, authenticity_score:int):
        if authenticity_score>=90 and deal_score>=90:
            return RecommendationSummary(deal_score,authenticity_score,"BUY_NOW",95,"excellent_authentic_deal")
        if authenticity_score<40:
            return RecommendationSummary(deal_score,authenticity_score,"AVOID",90,"possible_fake_discount")
        return RecommendationSummary(deal_score,authenticity_score,"WAIT",70,"better_price_likely")