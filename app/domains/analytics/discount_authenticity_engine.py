from dataclasses import dataclass


@dataclass
class DiscountAuthenticityResult:
    score:int
    verdict:str
    reason:str

class DiscountAuthenticityEngine:
    def evaluate(self, *, fake_discount_detected:bool, quality_score:int)->DiscountAuthenticityResult:
        if fake_discount_detected:
            return DiscountAuthenticityResult(10,"FAKE","fake_discount_detected")
        if quality_score>=90:
            return DiscountAuthenticityResult(95,"AUTHENTIC","excellent_real_discount")
        return DiscountAuthenticityResult(70,"LIKELY_AUTHENTIC","no_fake_pattern_detected")