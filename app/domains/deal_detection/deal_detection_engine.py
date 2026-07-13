from decimal import Decimal


class DealDetectionEngine:
    def detect(self, *, product_key: str, offer: dict, price_history: dict | None = None, personalization: dict | None = None) -> dict:
        score = 50
        reasons: list[str] = []
        next_actions: list[str] = []

        offer_price = Decimal(str(offer.get("price") or offer.get("base_price") or "0"))

        price_signal = "UNKNOWN"
        if price_history and price_history.get("min_price") is not None:
            min_price = Decimal(str(price_history["min_price"]))
            average_price = Decimal(str(price_history.get("average_price") or min_price))
            latest_price = Decimal(str(price_history.get("latest_price") or offer_price))

            if offer_price <= min_price:
                score += 25
                price_signal = "AT_OR_BELOW_HISTORY_LOW"
                reasons.append("PRICE_AT_HISTORY_LOW")
            elif offer_price < average_price:
                score += 15
                price_signal = "BELOW_AVERAGE"
                reasons.append("PRICE_BELOW_AVERAGE")
            elif latest_price > average_price:
                score -= 10
                price_signal = "ABOVE_AVERAGE"
                reasons.append("PRICE_ABOVE_AVERAGE")
            else:
                score += 5
                price_signal = "NORMAL"
                reasons.append("PRICE_NORMAL")

            if price_history.get("trend") == "DOWN":
                score += 10
                reasons.append("PRICE_TREND_DOWN")
            elif price_history.get("trend") == "UP":
                score -= 5
                reasons.append("PRICE_TREND_UP")

        personalization_signal = "UNKNOWN"
        if personalization and personalization.get("top_offer"):
            p_score = personalization["top_offer"].get("personalization_score", 0)
            if p_score >= 85:
                score += 15
                personalization_signal = "STRONG_MATCH"
                reasons.append("STRONG_PERSONALIZATION_MATCH")
            elif p_score >= 60:
                score += 5
                personalization_signal = "MODERATE_MATCH"
                reasons.append("MODERATE_PERSONALIZATION_MATCH")
            else:
                score -= 10
                personalization_signal = "WEAK_MATCH"
                reasons.append("WEAK_PERSONALIZATION_MATCH")

        score = max(0, min(100, score))

        if score >= 85:
            level = "EXCELLENT_DEAL"
            next_actions.append("Buy now if seller terms are acceptable.")
        elif score >= 70:
            level = "GOOD_DEAL"
            next_actions.append("Consider buying after checking warranty and delivery.")
        elif score >= 55:
            level = "FAIR_DEAL"
            next_actions.append("Compare with at least one more marketplace.")
        else:
            level = "WEAK_DEAL"
            next_actions.append("Wait for a better price or stronger signal.")

        if not reasons:
            reasons.append("INSUFFICIENT_DEAL_SIGNALS")

        return {
            "deal_level": level,
            "deal_score": score,
            "price_signal": price_signal,
            "personalization_signal": personalization_signal,
            "confidence": score,
            "reasons": reasons,
            "next_actions": next_actions,
        }
