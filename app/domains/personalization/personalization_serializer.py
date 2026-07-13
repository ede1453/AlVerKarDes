def serialize_profile(profile):
    return {
        "user_id": profile.user_id,
        "preferred_marketplaces": profile.preferred_marketplaces,
        "blocked_marketplaces": profile.blocked_marketplaces,
        "preferred_brands": profile.preferred_brands,
        "max_price": profile.max_price,
        "min_discount_percent": profile.min_discount_percent,
        "risk_tolerance": profile.risk_tolerance,
        "metadata": profile.metadata,
        "updated_at": profile.updated_at.isoformat(),
    }


def serialize_offer_score(score):
    return {
        "offer_id": score.offer_id,
        "marketplace": score.marketplace,
        "product_name": score.product_name,
        "base_price": score.base_price,
        "personalization_score": score.personalization_score,
        "reasons": score.reasons,
        "metadata": score.metadata,
    }


def serialize_personalization_result(result):
    return {
        "user_id": result.user_id,
        "scored_count": result.scored_count,
        "top_offer": result.top_offer,
        "offers": [serialize_offer_score(offer) for offer in result.offers],
        "metadata": result.metadata,
    }
