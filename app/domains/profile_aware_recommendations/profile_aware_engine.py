class ProfileAwareRecommendationEngine:
    def enrich_signals(self, *, profile_context: dict, base_recommendations: list[dict]):
        preferred_products = set(profile_context.get("preferred_product_keys", []))
        avoided_products = set(profile_context.get("avoided_product_keys", []))
        preferred_marketplaces = set(profile_context.get("preferred_marketplaces", []))
        blocked_marketplaces = set(profile_context.get("blocked_marketplaces", []))
        preferred_brands = {brand.lower() for brand in profile_context.get("preferred_brands", [])}

        enriched = []
        for item in base_recommendations:
            source = item.get("source", {})
            product_key = item.get("product_key") or source.get("product_key")
            marketplace = item.get("marketplace") or source.get("marketplace")
            product_name = (item.get("product_name") or source.get("product_name") or "").lower()

            score = int(item.get("score", 50))
            rationale = list(item.get("rationale", []))

            if product_key in preferred_products:
                score += 12
                rationale.append("PROFILE_PREFERRED_PRODUCT")
            if product_key in avoided_products:
                score -= 25
                rationale.append("PROFILE_AVOIDED_PRODUCT")
            if marketplace in preferred_marketplaces:
                score += 10
                rationale.append("PROFILE_PREFERRED_MARKETPLACE")
            if marketplace in blocked_marketplaces:
                score -= 40
                rationale.append("PROFILE_BLOCKED_MARKETPLACE")
            if any(brand in product_name for brand in preferred_brands):
                score += 8
                rationale.append("PROFILE_PREFERRED_BRAND")

            enriched_item = dict(item)
            enriched_item["score"] = max(0, min(100, score))
            enriched_item["rationale"] = rationale
            enriched_item["profile_context_applied"] = True
            enriched.append(enriched_item)

        enriched.sort(key=lambda item: (-item.get("score", 0), item.get("product_name", "")))
        for index, item in enumerate(enriched, start=1):
            item["rank"] = index
            if item["score"] >= 85:
                item["recommendation_type"] = "BEST_CHOICE"
            elif item["score"] >= 70:
                item["recommendation_type"] = "GOOD_ALTERNATIVE"
            elif item["score"] >= 50:
                item["recommendation_type"] = "CONSIDER"
            else:
                item["recommendation_type"] = "AVOID_OR_WAIT"

        return {
            "status": "COMPLETED" if enriched else "NO_RECOMMENDATIONS",
            "items": enriched,
            "metadata": {
                "profile_context_version": profile_context.get("metadata", {}).get("context_version"),
                "profile_score": profile_context.get("profile_score", 0),
                "profile_aware_version": "profile_aware_recommendation_v1",
            },
        }
