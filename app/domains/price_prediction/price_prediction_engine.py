from decimal import ROUND_HALF_UP, Decimal


class PricePredictionEngine:
    def predict(self, *, product_key: str, price_history: dict, horizon_days: int = 7) -> dict:
        points = price_history.get("points", [])
        current_price = price_history.get("latest_price")
        trend = price_history.get("trend", "UNKNOWN")

        reasons: list[str] = []
        confidence = 45

        if not current_price or not points:
            return {
                "current_price": current_price,
                "predicted_price": current_price,
                "prediction_horizon_days": horizon_days,
                "direction": "UNKNOWN",
                "confidence": 20,
                "recommendation_hint": "INSUFFICIENT_HISTORY",
                "reasons": ["INSUFFICIENT_PRICE_HISTORY"],
            }

        current = Decimal(str(current_price))
        min_price = Decimal(str(price_history.get("min_price") or current))
        avg_price = Decimal(str(price_history.get("average_price") or current))
        max_price = Decimal(str(price_history.get("max_price") or current))

        if len(points) >= 2:
            confidence += 20
            reasons.append("MULTIPLE_PRICE_POINTS")

        if trend == "DOWN":
            predicted = max(min_price, current - ((current - min_price) * Decimal("0.25")))
            direction = "DOWN"
            confidence += 10
            reasons.append("RECENT_TREND_DOWN")
        elif trend == "UP":
            predicted = min(max_price, current + ((max_price - current) * Decimal("0.25")))
            direction = "UP"
            confidence += 5
            reasons.append("RECENT_TREND_UP")
        elif trend == "FLAT":
            predicted = avg_price
            direction = "FLAT"
            confidence += 5
            reasons.append("RECENT_TREND_FLAT")
        else:
            predicted = avg_price
            direction = "UNKNOWN"
            reasons.append("UNKNOWN_TREND")

        if current <= min_price:
            confidence += 10
            reasons.append("CURRENT_AT_HISTORY_LOW")
        elif current > avg_price:
            reasons.append("CURRENT_ABOVE_AVERAGE")
        else:
            reasons.append("CURRENT_NOT_ABOVE_AVERAGE")

        confidence = max(0, min(100, confidence))

        if direction == "UP" or current <= min_price:
            recommendation_hint = "BUY_SOON"
        elif direction == "DOWN":
            recommendation_hint = "WAIT_OR_WATCH"
        else:
            recommendation_hint = "WATCH"

        return {
            "current_price": str(current),
            "predicted_price": str(predicted.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)),
            "prediction_horizon_days": horizon_days,
            "direction": direction,
            "confidence": confidence,
            "recommendation_hint": recommendation_hint,
            "reasons": reasons,
        }
