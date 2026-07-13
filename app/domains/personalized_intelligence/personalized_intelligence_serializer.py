def serialize_personalized_decision(result):
    return {
        "user_id": result.user_id,
        "base_decision": result.base_decision,
        "personalized_decision": result.personalized_decision,
        "personalized_confidence": result.personalized_confidence,
        "personalization_reasons": result.personalization_reasons,
        "user_profile_snapshot": result.user_profile_snapshot,
    }


def serialize_user_profile(profile):
    return {
        "user_id": profile.user_id,
        "preferred_brands": profile.preferred_brands,
        "avoided_brands": profile.avoided_brands,
        "preferred_categories": profile.preferred_categories,
        "price_sensitivity": profile.price_sensitivity,
        "minimum_confidence": profile.minimum_confidence,
    }
