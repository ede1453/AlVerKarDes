from dataclasses import dataclass
from urllib.parse import urlparse


@dataclass
class FraudInput:
    offer_url: str
    current_price: float
    historical_avg_price: float | None = None
    store_name: str | None = None
    store_trust_score: float | None = None


@dataclass
class FraudResult:
    risk_level: str
    risk_score: float
    flags: list[str]
    confidence: float
    uncertainty: dict


class FraudAgent:
    SUSPICIOUS_TLDS = [".xyz", ".click", ".top", ".shop"]

    def run(self, payload: FraudInput) -> FraudResult:
        flags = []
        score = 0

        current_price = float(payload.current_price) if payload.current_price is not None else None
        historical_avg_price = float(payload.historical_avg_price) if payload.historical_avg_price is not None else None

        if historical_avg_price and current_price and current_price < historical_avg_price * 0.4:
            flags.append("UNREALISTIC_DISCOUNT")
            score += 35
        if payload.store_trust_score is not None and payload.store_trust_score < 40:
            flags.append("LOW_STORE_TRUST")
            score += 25

        domain = urlparse(payload.offer_url or "").netloc.lower()
        if domain and any(domain.endswith(tld) for tld in self.SUSPICIOUS_TLDS):
            flags.append("SUSPICIOUS_DOMAIN")
            score += 25
        if not payload.store_name:
            flags.append("UNKNOWN_SELLER")
            score += 15

        risk_level = "HIGH" if score >= 60 else "MEDIUM" if score >= 30 else "LOW"
        return FraudResult(risk_level, min(score, 100), flags, 85 if payload.historical_avg_price else 60, {"level": "LOW" if payload.historical_avg_price else "MEDIUM", "explanation": "Rule-based fraud heuristics."})
