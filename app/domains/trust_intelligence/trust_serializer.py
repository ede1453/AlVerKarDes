def serialize_trust_signal(signal):
    return {
        "source_type": signal.source_type,
        "source_id": signal.source_id,
        "positive_count": signal.positive_count,
        "negative_count": signal.negative_count,
        "neutral_count": signal.neutral_count,
        "fraud_count": signal.fraud_count,
        "return_count": signal.return_count,
        "total_count": signal.total_count,
    }


def serialize_trust_profile(profile):
    return {
        "entity_type": profile.entity_type,
        "entity_id": profile.entity_id,
        "trust_score": profile.trust_score,
        "reliability_score": profile.reliability_score,
        "positive_count": profile.positive_count,
        "negative_count": profile.negative_count,
        "fraud_count": profile.fraud_count,
        "last_updated": profile.last_updated.isoformat(),
    }


def serialize_trust_evaluation(result):
    return {
        "decision_id": result.decision_id,
        "user_trust_score": result.user_trust_score,
        "community_score": result.community_score,
        "store_score": result.store_score,
        "product_score": result.product_score,
        "recommendation_confidence_adjustment": result.recommendation_confidence_adjustment,
        "final_confidence": result.final_confidence,
        "risk_modifier": result.risk_modifier,
        "reason_codes": result.reason_codes,
    }
