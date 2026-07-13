class AIShoppingAgentEngine:
    def decide(
        self,
        *,
        query: str,
        user_id: str | None,
        search: dict | None,
        matching: dict | None,
        price_history: dict | None,
        personalization: dict | None,
    ) -> dict:
        reasons: list[str] = []
        next_actions: list[str] = []

        top_offer = None
        if personalization and personalization.get("top_offer"):
            top_offer = personalization["top_offer"]
            reasons.append("PERSONALIZED_TOP_OFFER")
        elif search and search.get("top_offer"):
            top_offer = search["top_offer"]
            reasons.append("SEARCH_TOP_OFFER")

        score = 50

        if search and search.get("status") == "FOUND":
            score += 15
            reasons.append("SEARCH_FOUND_CANDIDATES")

        if matching and matching.get("group_count", 0) > 0:
            score += 10
            reasons.append("MATCHED_PRODUCT_GROUP")

        if price_history:
            trend = price_history.get("trend")
            if trend == "DOWN":
                score += 15
                reasons.append("PRICE_TREND_DOWN")
            elif trend == "UP":
                score -= 10
                reasons.append("PRICE_TREND_UP")
            elif trend == "FLAT":
                score += 5
                reasons.append("PRICE_TREND_FLAT")

        if personalization and personalization.get("top_offer"):
            personalization_score = personalization["top_offer"].get("personalization_score", 0)
            if personalization_score >= 85:
                score += 15
                reasons.append("HIGH_PERSONALIZATION_SCORE")
            elif personalization_score < 40:
                score -= 20
                reasons.append("LOW_PERSONALIZATION_SCORE")

        score = max(0, min(100, score))

        if score >= 80:
            decision = "BUY_NOW"
            next_actions.append("Check final seller terms before purchase.")
            next_actions.append("Confirm warranty, return policy, and delivery cost.")
        elif score >= 60:
            decision = "CONSIDER"
            next_actions.append("Compare at least one more marketplace before buying.")
            next_actions.append("Set a price alert if you are not in a hurry.")
        else:
            decision = "WAIT"
            next_actions.append("Wait for a better price or stronger trust signals.")
            next_actions.append("Track price history before purchasing.")

        if not reasons:
            reasons.append("INSUFFICIENT_SIGNALS")

        return {
            "query": query,
            "user_id": user_id,
            "decision": decision,
            "confidence": score,
            "top_offer": top_offer,
            "reasons": reasons,
            "next_actions": next_actions,
        }
