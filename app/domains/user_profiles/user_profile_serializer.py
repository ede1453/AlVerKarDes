def serialize_user_profile(profile):
    return {
        "user_id": profile.user_id,
        "preferred_product_keys": profile.preferred_product_keys,
        "avoided_product_keys": profile.avoided_product_keys,
        "preferred_marketplaces": profile.preferred_marketplaces,
        "blocked_marketplaces": profile.blocked_marketplaces,
        "preferred_brands": profile.preferred_brands,
        "risk_tolerance": profile.risk_tolerance,
        "profile_score": profile.profile_score,
        "metadata": profile.metadata,
        "updated_at": profile.updated_at.isoformat(),
    }
