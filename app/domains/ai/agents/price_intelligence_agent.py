from dataclasses import dataclass
from statistics import mean


@dataclass
class PricePoint:
    amount: float
    currency: str
    observed_at: str | None = None


@dataclass
class PriceIntelligenceInput:
    current_price: PricePoint
    price_history: list[PricePoint]


@dataclass
class PriceIntelligenceResult:
    discount_quality: str
    price_signal: str
    confidence: float
    summary: str
    evidence: list[dict]
    uncertainty: dict


class PriceIntelligenceAgent:
    def run(self, payload: PriceIntelligenceInput) -> PriceIntelligenceResult:
        current = payload.current_price.amount
        history = [p.amount for p in payload.price_history if p.amount > 0]

        if len(history) < 5:
            return PriceIntelligenceResult("UNKNOWN", "INSUFFICIENT_DATA", 20, "Not enough price history.", [], {"level": "HIGH", "explanation": "Fewer than 5 historical prices."})

        lowest = min(history)
        avg = mean(history)
        discount = (avg - current) / avg * 100 if avg else 0
        above_lowest = (current - lowest) / lowest * 100 if lowest else 0

        quality = "EXCELLENT" if current <= lowest else "GOOD" if discount >= 25 and above_lowest <= 10 else "NORMAL" if discount >= 10 else "WEAK" if discount > 0 else "FAKE_OR_MISLEADING"
        signal = "BUY" if quality in {"EXCELLENT", "GOOD"} else "WAIT"
        confidence = min(95, 50 + len(history) * 2)
        summary = f"Current price is {current:.2f} {payload.current_price.currency}. Historical lowest is {lowest:.2f}. Average is {avg:.2f}."

        return PriceIntelligenceResult(
            quality,
            signal,
            confidence,
            summary,
            [{
                "type": "PRICE_HISTORY",
                "title": "Historical price comparison",
                "data": {
                    "current_price": current,
                    "historical_lowest": lowest,
                    "historical_average": round(avg, 2),
                    "history_points": len(history),
                    "currency": payload.current_price.currency,
                },
                "confidence": confidence,
            }],
            {"level": "LOW" if len(history) >= 30 else "MEDIUM", "explanation": "Based on stored price history."},
        )
