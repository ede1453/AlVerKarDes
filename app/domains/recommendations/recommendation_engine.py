from decimal import Decimal


class RecommendationEngine:
    def recommend(
        self,
        *,
        query: str,
        user_id: str | None,
        candidates: list[dict],
        personalization: dict | None = None,
        discount_intelligence: dict | None = None,
        deal_detection: dict | None = None,
        price_prediction: dict | None = None,
    ):
        scored = []

        for candidate in candidates:
            score, rationale, rec_type = self._score_candidate(
                candidate=candidate,
                personalization=personalization,
                discount_intelligence=discount_intelligence,
                deal_detection=deal_detection,
                price_prediction=price_prediction,
            )
            scored.append(
                {
                    "candidate": candidate,
                    "score": score,
                    "rationale": rationale,
                    "recommendation_type": rec_type,
                }
            )

        scored = sorted(
            scored,
            key=lambda item: (
                -item["score"],
                Decimal(str(item["candidate"].get("price") or "999999")),
                item["candidate"].get("product_name", ""),
            ),
        )

        if not scored:
            return {
                "status": "NO_RECOMMENDATIONS",
                "items": [],
                "next_actions": ["Add more candidates or broaden the search query."],
            }

        return {
            "status": "COMPLETED",
            "items": scored,
            "next_actions": [
                "Compare the top recommendation with the current best deal.",
                "Check warranty, seller terms, and final checkout price before buying.",
            ],
        }

    def _score_candidate(
        self,
        *,
        candidate: dict,
        personalization: dict | None,
        discount_intelligence: dict | None,
        deal_detection: dict | None,
        price_prediction: dict | None,
    ):
        score = 50
        rationale: list[str] = []

        if candidate.get("canonical_confidence", 0) >= 90:
            score += 10
            rationale.append("HIGH_CANONICAL_CONFIDENCE")

        if candidate.get("price") is not None:
            score += 5
            rationale.append("HAS_PRICE")

        if personalization and personalization.get("top_offer"):
            top = personalization["top_offer"]
            if top.get("marketplace") == candidate.get("marketplace"):
                score += 15
                rationale.append("MATCHES_PERSONALIZED_MARKETPLACE")

        if discount_intelligence:
            quality = discount_intelligence.get("discount_quality")
            fake_risk = discount_intelligence.get("fake_discount_risk")
            if quality in ["EXCELLENT_REAL_DISCOUNT", "GOOD_DISCOUNT"]:
                score += 15
                rationale.append("STRONG_DISCOUNT_SIGNAL")
            if fake_risk == "HIGH":
                score -= 25
                rationale.append("HIGH_FAKE_DISCOUNT_RISK")
            elif fake_risk == "LOW":
                score += 5
                rationale.append("LOW_FAKE_DISCOUNT_RISK")

        if deal_detection:
            deal_level = deal_detection.get("deal_level")
            if deal_level == "EXCELLENT_DEAL":
                score += 15
                rationale.append("EXCELLENT_DEAL_SIGNAL")
            elif deal_level == "WEAK_DEAL":
                score -= 15
                rationale.append("WEAK_DEAL_SIGNAL")

        if price_prediction:
            hint = price_prediction.get("recommendation_hint")
            if hint == "BUY_SOON":
                score += 10
                rationale.append("PRICE_PREDICTION_BUY_SOON")
            elif hint == "WAIT_OR_WATCH":
                score -= 5
                rationale.append("PRICE_PREDICTION_WAIT")

        score = max(0, min(100, score))

        if score >= 85:
            rec_type = "BEST_CHOICE"
        elif score >= 70:
            rec_type = "GOOD_ALTERNATIVE"
        elif score >= 50:
            rec_type = "CONSIDER"
        else:
            rec_type = "AVOID_OR_WAIT"

        if not rationale:
            rationale.append("NEUTRAL_RECOMMENDATION")

        return score, rationale, rec_type
