from dataclasses import dataclass, field
from typing import Any


@dataclass
class DecisionSignal:
    name: str
    value: Any
    confidence: float = 0.0
    weight: float = 0.0


@dataclass
class ConsumerDecisionInput:
    price_signal: str
    price_confidence: float
    fake_discount_risk: str = "UNKNOWN"
    review_reliability: str = "UNKNOWN"
    fraud_risk: str = "UNKNOWN"
    match_confidence: float = 0.0
    availability: str | None = None
    current_price: float | None = None
    historical_lowest: float | None = None
    historical_average: float | None = None
    store_trust_score: float = 80.0
    extra: dict = field(default_factory=dict)


@dataclass
class ConsumerDecisionOutput:
    decision: str
    score: float
    confidence: float
    reasons: list[str]
    risks: list[str]
    recommended_action: str
    signals: dict


class ConsumerDecisionEngine:
    def decide(self, payload: ConsumerDecisionInput) -> ConsumerDecisionOutput:
        score = 50.0
        reasons: list[str] = []
        risks: list[str] = []

        price_score = self._price_score(payload.price_signal, payload.price_confidence)
        score += price_score

        if payload.price_signal == "BUY":
            reasons.append("Price history supports buying now.")
        elif payload.price_signal == "WAIT":
            risks.append("Price history suggests waiting.")
        elif payload.price_signal == "INSUFFICIENT_HISTORY":
            risks.append("Price history is insufficient.")

        fake_discount_penalty = self._fake_discount_penalty(payload.fake_discount_risk)
        score -= fake_discount_penalty

        if payload.fake_discount_risk == "HIGH":
            risks.append("Possible fake discount pattern detected.")
        elif payload.fake_discount_risk == "LOW":
            reasons.append("No strong fake discount pattern detected.")

        fraud_penalty = self._fraud_penalty(payload.fraud_risk)
        score -= fraud_penalty

        if payload.fraud_risk == "HIGH":
            risks.append("High fraud risk.")
        elif payload.fraud_risk == "LOW":
            reasons.append("Fraud risk is low.")

        if payload.match_confidence >= 90:
            score += 8
            reasons.append("Product identity match is strong.")
        elif payload.match_confidence < 60:
            score -= 15
            risks.append("Product identity confidence is weak.")

        if payload.store_trust_score >= 85:
            score += 5
            reasons.append("Store trust score is high.")
        elif payload.store_trust_score < 50:
            score -= 15
            risks.append("Store trust score is low.")

        if payload.availability and payload.availability.lower() in {"in_stock", "available"}:
            score += 4
            reasons.append("Product is available.")
        elif payload.availability and payload.availability.lower() in {"out_of_stock", "unavailable"}:
            score -= 20
            risks.append("Product is not available.")

        score = max(0.0, min(100.0, round(score, 2)))
        confidence = self._confidence(payload=payload, score=score)
        decision = self._decision(score=score, payload=payload)
        recommended_action = self._recommended_action(decision)

        return ConsumerDecisionOutput(
            decision=decision,
            score=score,
            confidence=confidence,
            reasons=reasons,
            risks=risks,
            recommended_action=recommended_action,
            signals={
                "price_signal": payload.price_signal,
                "price_confidence": payload.price_confidence,
                "fake_discount_risk": payload.fake_discount_risk,
                "fraud_risk": payload.fraud_risk,
                "review_reliability": payload.review_reliability,
                "match_confidence": payload.match_confidence,
                "store_trust_score": payload.store_trust_score,
                "availability": payload.availability,
                "current_price": payload.current_price,
                "historical_lowest": payload.historical_lowest,
                "historical_average": payload.historical_average,
            },
        )

    def _price_score(self, signal: str, confidence: float) -> float:
        confidence_factor = max(0.0, min(confidence, 100.0)) / 100.0

        if signal == "BUY":
            return 28 * confidence_factor
        if signal == "WAIT":
            return -25 * confidence_factor
        if signal == "NEUTRAL":
            return 0
        if signal == "INSUFFICIENT_HISTORY":
            return -8
        return -10

    def _fake_discount_penalty(self, risk: str) -> float:
        return {
            "LOW": 0,
            "MEDIUM": 10,
            "HIGH": 30,
            "UNKNOWN": 8,
        }.get(risk, 8)

    def _fraud_penalty(self, risk: str) -> float:
        return {
            "LOW": 0,
            "MEDIUM": 15,
            "HIGH": 35,
            "UNKNOWN": 8,
        }.get(risk, 8)

    def _confidence(self, *, payload: ConsumerDecisionInput, score: float) -> float:
        parts = [
            payload.price_confidence,
            payload.match_confidence,
            payload.store_trust_score,
        ]

        if payload.fake_discount_risk != "UNKNOWN":
            parts.append(80)

        if payload.fraud_risk != "UNKNOWN":
            parts.append(80)

        return round(max(0.0, min(100.0, sum(parts) / len(parts))), 2)

    def _decision(self, *, score: float, payload: ConsumerDecisionInput) -> str:
        if payload.fraud_risk == "HIGH" or payload.fake_discount_risk == "HIGH":
            return "AVOID"

        if payload.price_signal == "INSUFFICIENT_HISTORY" and score < 65:
            return "INSUFFICIENT_DATA"

        if score >= 75:
            return "BUY_NOW"

        if score >= 50:
            return "WAIT"

        return "AVOID"

    def _recommended_action(self, decision: str) -> str:
        return {
            "BUY_NOW": "Buy now if this product fits your needs.",
            "WAIT": "Wait and monitor price changes.",
            "AVOID": "Do not buy this offer.",
            "INSUFFICIENT_DATA": "Collect more price and product evidence before deciding.",
        }.get(decision, "Review manually.")
