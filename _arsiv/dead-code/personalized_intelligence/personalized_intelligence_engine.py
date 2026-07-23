from app.domains.personalized_intelligence.personalization_models import (
    PersonalizedDecisionInput,
    PersonalizedDecisionResult,
    UserPreferenceProfile,
)


class PersonalizedIntelligenceEngine:
    def personalize(
        self,
        *,
        profile: UserPreferenceProfile,
        decision: PersonalizedDecisionInput,
    ) -> PersonalizedDecisionResult:
        personalized_decision = decision.final_decision
        confidence = decision.confidence
        reasons: list[str] = []

        if decision.product_brand and decision.product_brand in profile.avoided_brands:
            personalized_decision = "AVOID"
            confidence = max(confidence, 90)
            reasons.append("USER_AVOIDS_BRAND")

        if decision.product_brand and decision.product_brand in profile.preferred_brands:
            confidence = min(99, confidence + 5)
            reasons.append("USER_PREFERS_BRAND")

        if decision.product_category and decision.product_category in profile.preferred_categories:
            confidence = min(99, confidence + 3)
            reasons.append("USER_PREFERS_CATEGORY")

        if profile.price_sensitivity == "HIGH" and decision.final_decision == "BUY_NOW":
            if decision.opportunity_level != "HIGH":
                personalized_decision = "WATCH"
                confidence = max(70, confidence - 10)
                reasons.append("HIGH_PRICE_SENSITIVITY_REQUIRES_STRONG_OPPORTUNITY")

        if confidence < profile.minimum_confidence and personalized_decision == "BUY_NOW":
            personalized_decision = "WATCH"
            reasons.append("BELOW_USER_MINIMUM_CONFIDENCE")

        if not reasons:
            reasons.append("NO_PERSONALIZATION_ADJUSTMENT")

        return PersonalizedDecisionResult(
            user_id=profile.user_id,
            base_decision=decision.final_decision,
            personalized_decision=personalized_decision,
            personalized_confidence=confidence,
            personalization_reasons=reasons,
            user_profile_snapshot={
                "preferred_brands": list(profile.preferred_brands),
                "avoided_brands": list(profile.avoided_brands),
                "preferred_categories": list(profile.preferred_categories),
                "price_sensitivity": profile.price_sensitivity,
                "minimum_confidence": profile.minimum_confidence,
            },
        )
