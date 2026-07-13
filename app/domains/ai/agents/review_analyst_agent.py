from collections import Counter
from dataclasses import dataclass


@dataclass
class ReviewInput:
    reviews: list[str]
    source_name: str | None = None
    source_url: str | None = None


@dataclass
class ReviewAnalysisResult:
    pros: list[str]
    cons: list[str]
    recurring_complaints: list[str]
    review_reliability: str
    confidence: float
    evidence: list[dict]
    uncertainty: dict


class ReviewAnalystAgent:
    POSITIVE_KEYWORDS = ["good", "great", "excellent", "fast", "quiet", "reliable", "solid", "iyi", "harika", "mükemmel", "hızlı", "sessiz", "kaliteli"]
    NEGATIVE_KEYWORDS = ["bad", "poor", "slow", "noisy", "broken", "defective", "overheating", "kötü", "yavaş", "gürültülü", "bozuk", "ısınma", "arıza", "pil"]
    COMPLAINT_PATTERNS = {
        "battery": ["battery", "pil", "şarj"],
        "noise": ["noise", "noisy", "gürültü", "sesli"],
        "overheating": ["overheating", "heat", "ısınma", "sıcak"],
        "performance": ["slow", "lag", "yavaş", "donma"],
        "delivery": ["delivery", "shipping", "kargo", "teslimat"],
    }

    def run(self, payload: ReviewInput) -> ReviewAnalysisResult:
        reviews = [r.strip() for r in payload.reviews if r and r.strip()]
        if len(reviews) < 5:
            return ReviewAnalysisResult([], [], [], "LOW", 25, [], {"level": "HIGH", "explanation": "Fewer than 5 reviews are available."})

        pros = [r[:280] for r in reviews if any(k in r.lower() for k in self.POSITIVE_KEYWORDS)]
        cons = [r[:280] for r in reviews if any(k in r.lower() for k in self.NEGATIVE_KEYWORDS)]
        complaints = self._complaints(reviews)
        reliability = "HIGH" if len(reviews) >= 100 else "MEDIUM" if len(reviews) >= 20 else "LOW"
        confidence = min(90, {"HIGH": 80, "MEDIUM": 60, "LOW": 35}[reliability] + min(len(reviews) / 10, 10))

        return ReviewAnalysisResult(
            pros[:5],
            cons[:5],
            complaints,
            reliability,
            confidence,
            [{
                "type": "REVIEW_ANALYSIS",
                "title": "Review pattern analysis",
                "source_name": payload.source_name,
                "source_url": payload.source_url,
                "data": {"review_count": len(reviews), "recurring_complaints": complaints},
                "confidence": confidence,
            }],
            {"level": "LOW" if confidence >= 75 else "MEDIUM", "explanation": "Review analysis is based on provided review text."},
        )

    def _complaints(self, reviews: list[str]) -> list[str]:
        counter = Counter()
        lowered = [r.lower() for r in reviews]
        for complaint, keywords in self.COMPLAINT_PATTERNS.items():
            for review in lowered:
                if any(keyword in review for keyword in keywords):
                    counter[complaint] += 1
        return [item for item, count in counter.items() if count >= 2]
