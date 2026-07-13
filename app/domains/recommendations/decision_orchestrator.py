from dataclasses import dataclass


@dataclass
class DecisionInput:
    product_confidence: float
    price_signal: str
    price_confidence: float
    review_confidence: float | None = None
    review_reliability: str | None = None
    fraud_risk_level: str | None = None
    fraud_score: float | None = None


@dataclass
class DecisionOutput:
    decision: str
    confidence: float
    reasons: list[dict]
    uncertainty: dict


class DecisionOrchestrator:
    def decide(self, payload: DecisionInput) -> DecisionOutput:
        if payload.fraud_risk_level == "HIGH":
            return DecisionOutput(
                "DO_NOT_BUY",
                max(80, payload.fraud_score or 80),
                [{"type": "FRAUD_RISK", "title": "High fraud risk detected", "description": "The offer has strong suspicious indicators.", "weight": -1.0}],
                {"level": "LOW", "explanation": "High fraud risk overrides buy signals."},
            )

        if payload.product_confidence < 50:
            return DecisionOutput(
                "INSUFFICIENT_DATA",
                30,
                [{"type": "PRODUCT_IDENTITY", "title": "Product identity is weak", "description": "The system cannot confidently identify the product.", "weight": -0.8}],
                {"level": "HIGH", "explanation": "Product identity confidence is too low."},
            )

        reasons = []
        if payload.price_signal == "BUY":
            decision = "BUY"
            confidence = min(payload.product_confidence, payload.price_confidence)
            reasons.append({"type": "PRICE_SIGNAL", "title": "Price signal supports buying", "description": "Stored price history indicates this may be a good buying moment.", "weight": 0.7})
        elif payload.price_signal == "WAIT":
            decision = "WAIT"
            confidence = min(payload.product_confidence, payload.price_confidence)
            reasons.append({"type": "PRICE_SIGNAL", "title": "Price signal supports waiting", "description": "The current price is not strong enough compared to historical data.", "weight": -0.4})
        else:
            decision = "INSUFFICIENT_DATA"
            confidence = 35
            reasons.append({"type": "PRICE_DATA", "title": "Price data is insufficient", "description": "The system cannot judge the offer without sufficient historical data.", "weight": -0.7})

        if payload.review_reliability == "LOW":
            confidence = min(confidence, 70)
            reasons.append({"type": "REVIEW_RELIABILITY", "title": "Review reliability is low", "description": "Review evidence is limited and should not be overtrusted.", "weight": -0.2})

        if payload.fraud_risk_level == "MEDIUM":
            confidence = min(confidence, 65)
            reasons.append({"type": "FRAUD_RISK", "title": "Medium fraud risk", "description": "The offer has some risk indicators. Proceed carefully.", "weight": -0.5})

        uncertainty_level = "LOW" if confidence >= 75 else "MEDIUM" if confidence >= 50 else "HIGH"
        return DecisionOutput(decision, confidence, reasons, {"level": uncertainty_level, "explanation": "Decision combines product, price, review and fraud signals."})
