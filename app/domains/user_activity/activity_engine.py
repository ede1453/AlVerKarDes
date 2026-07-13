POSITIVE_EVENTS = {
    "recommendation_clicked",
    "watchlist_added",
    "alert_opened",
    "purchase_intent",
    "liked",
}

NEGATIVE_EVENTS = {
    "dismissed",
    "not_interested",
    "blocked_product",
    "alert_muted",
    "disliked",
}


class UserActivityEngine:
    def summarize(self, *, user_id: str, events: list):
        positive_count = 0
        negative_count = 0
        neutral_count = 0
        product_scores: dict[str, int] = {}

        for event in events:
            product_key = event.product_key
            if event.event_type in POSITIVE_EVENTS:
                positive_count += 1
                if product_key:
                    product_scores[product_key] = product_scores.get(product_key, 0) + 1
            elif event.event_type in NEGATIVE_EVENTS:
                negative_count += 1
                if product_key:
                    product_scores[product_key] = product_scores.get(product_key, 0) - 1
            else:
                neutral_count += 1

        preferred = [
            product_key
            for product_key, score in sorted(product_scores.items(), key=lambda item: (-item[1], item[0]))
            if score > 0
        ]
        avoided = [
            product_key
            for product_key, score in sorted(product_scores.items(), key=lambda item: (item[1], item[0]))
            if score < 0
        ]

        return {
            "user_id": user_id,
            "event_count": len(events),
            "positive_count": positive_count,
            "negative_count": negative_count,
            "neutral_count": neutral_count,
            "preferred_product_keys": preferred,
            "avoided_product_keys": avoided,
            "metadata": {"activity_engine_version": "user_activity_v1"},
        }

    def recommendation_adjustment(self, *, summary: dict, recommendations: list[dict]):
        adjusted = []
        preferred = set(summary.get("preferred_product_keys", []))
        avoided = set(summary.get("avoided_product_keys", []))

        for item in recommendations:
            product_key = item.get("product_key") or item.get("source", {}).get("product_key")
            score = int(item.get("score", 50))
            reasons = list(item.get("rationale", []))

            if product_key in preferred:
                score += 10
                reasons.append("USER_ACTIVITY_POSITIVE_SIGNAL")
            if product_key in avoided:
                score -= 20
                reasons.append("USER_ACTIVITY_NEGATIVE_SIGNAL")

            adjusted_item = dict(item)
            adjusted_item["score"] = max(0, min(100, score))
            adjusted_item["rationale"] = reasons
            adjusted.append(adjusted_item)

        adjusted.sort(key=lambda item: (-item.get("score", 0), item.get("product_name", "")))
        for index, item in enumerate(adjusted, start=1):
            item["rank"] = index

        return {
            "status": "COMPLETED",
            "adjusted_count": len(adjusted),
            "items": adjusted,
            "metadata": {"adjustment_version": "user_activity_adjustment_v1"},
        }
