from decimal import ROUND_HALF_UP, Decimal


class DiscountIntelligenceEngine:
    def analyze(
        self,
        *,
        product_key: str,
        current_price: str | None,
        claimed_original_price: str | None = None,
        price_history: dict | None = None,
        deal_detection: dict | None = None,
        price_prediction: dict | None = None,
    ) -> dict:
        reasons: list[str] = []
        score = 50
        fake_risk_score = 30

        if current_price is None:
            return {
                "current_price": None,
                "claimed_original_price": claimed_original_price,
                "effective_discount_percent": None,
                "discount_quality": "UNKNOWN",
                "fake_discount_risk": "UNKNOWN",
                "confidence": 20,
                "reasons": ["MISSING_CURRENT_PRICE"],
            }

        current = Decimal(str(current_price))
        claimed = Decimal(str(claimed_original_price)) if claimed_original_price is not None else None

        effective_discount_percent = None
        if claimed and claimed > 0 and claimed > current:
            effective_discount_percent = int(((claimed - current) / claimed * Decimal("100")).quantize(Decimal("1"), rounding=ROUND_HALF_UP))
            reasons.append("CLAIMED_DISCOUNT_PRESENT")
            score += min(20, effective_discount_percent)
        elif claimed is not None:
            reasons.append("INVALID_OR_NO_CLAIMED_DISCOUNT")
            fake_risk_score += 20

        if price_history:
            min_price = Decimal(str(price_history.get("min_price") or current))
            avg_price = Decimal(str(price_history.get("average_price") or current))
            max_price = Decimal(str(price_history.get("max_price") or current))

            if current <= min_price:
                score += 25
                fake_risk_score -= 20
                reasons.append("CURRENT_AT_OR_BELOW_HISTORY_LOW")
            elif current < avg_price:
                score += 15
                fake_risk_score -= 10
                reasons.append("CURRENT_BELOW_AVERAGE_PRICE")
            else:
                score -= 10
                fake_risk_score += 20
                reasons.append("CURRENT_NOT_BELOW_AVERAGE")

            if claimed and claimed > max_price:
                fake_risk_score += 25
                reasons.append("CLAIMED_ORIGINAL_ABOVE_HISTORY_MAX")

            if price_history.get("trend") == "DOWN":
                score += 5
                reasons.append("PRICE_TREND_DOWN")
            elif price_history.get("trend") == "UP":
                score -= 5
                fake_risk_score += 5
                reasons.append("PRICE_TREND_UP")

        if deal_detection:
            deal_score = int(deal_detection.get("deal_score") or 0)
            if deal_score >= 85:
                score += 15
                reasons.append("HIGH_DEAL_SCORE")
            elif deal_score < 50:
                score -= 10
                fake_risk_score += 10
                reasons.append("LOW_DEAL_SCORE")

        if price_prediction:
            hint = price_prediction.get("recommendation_hint")
            if hint == "BUY_SOON":
                score += 10
                fake_risk_score -= 5
                reasons.append("PREDICTION_BUY_SOON")
            elif hint == "WAIT_OR_WATCH":
                score -= 5
                fake_risk_score += 5
                reasons.append("PREDICTION_WAIT_OR_WATCH")

        score = max(0, min(100, score))
        fake_risk_score = max(0, min(100, fake_risk_score))

        if score >= 85:
            quality = "EXCELLENT_REAL_DISCOUNT"
        elif score >= 70:
            quality = "GOOD_DISCOUNT"
        elif score >= 50:
            quality = "FAIR_DISCOUNT"
        else:
            quality = "WEAK_DISCOUNT"

        if fake_risk_score >= 70:
            fake_risk = "HIGH"
        elif fake_risk_score >= 40:
            fake_risk = "MEDIUM"
        else:
            fake_risk = "LOW"

        if not reasons:
            reasons.append("INSUFFICIENT_DISCOUNT_SIGNALS")

        return {
            "current_price": str(current),
            "claimed_original_price": None if claimed is None else str(claimed),
            "effective_discount_percent": effective_discount_percent,
            "discount_quality": quality,
            "fake_discount_risk": fake_risk,
            "confidence": score,
            "reasons": reasons,
        }
