from dataclasses import dataclass

from app.domains.products.intelligence.spec_extractor import ProductSpecExtractor


@dataclass
class ProductMatchScore:
    score: int
    decision: str
    reasons: list[str]


class ProductMatchScorer:
    def __init__(self):
        self.extractor = ProductSpecExtractor()

    def score_titles(self, left_title: str, right_title: str) -> ProductMatchScore:
        left = self.extractor.extract(left_title)
        right = self.extractor.extract(right_title)
        return self.score_specs(left, right)

    def score_specs(self, left, right) -> ProductMatchScore:
        score = 0
        reasons: list[str] = []

        score += self._score_equal(left.brand, right.brand, 20, "brand_match", "brand_mismatch", reasons)
        score += self._score_equal(left.model_family, right.model_family, 25, "model_family_match", "model_family_mismatch", reasons)
        score += self._score_equal(left.chip, right.chip, 15, "chip_match", "chip_mismatch", reasons)
        score += self._score_equal(left.ram_gb, right.ram_gb, 15, "ram_match", "ram_mismatch", reasons)
        score += self._score_equal(left.storage_gb, right.storage_gb, 20, "storage_match", "storage_mismatch", reasons)

        if left.color and right.color and left.color == right.color:
            score += 5
            reasons.append("color_match")
        elif left.color and right.color and left.color != right.color:
            reasons.append("color_mismatch")

        if score >= 90:
            decision = "MATCH"
        elif score >= 70:
            decision = "POSSIBLE_MATCH"
        else:
            decision = "NO_MATCH"

        return ProductMatchScore(score=score, decision=decision, reasons=reasons)

    def _score_equal(self, left, right, points: int, match_reason: str, mismatch_reason: str, reasons: list[str]) -> int:
        if left is None or right is None:
            reasons.append(f"{mismatch_reason}:missing")
            return 0

        if left == right:
            reasons.append(match_reason)
            return points

        reasons.append(mismatch_reason)
        return 0
