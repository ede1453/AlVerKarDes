def serialize_activity_event(event):
    return {
        "activity_id": event.activity_id,
        "user_id": event.user_id,
        "event_type": event.event_type,
        "product_key": event.product_key,
        "recommendation_id": event.recommendation_id,
        "metadata": event.metadata,
        "created_at": event.created_at.isoformat(),
    }


def serialize_feedback_summary(summary):
    return {
        "user_id": summary.user_id,
        "event_count": summary.event_count,
        "positive_count": summary.positive_count,
        "negative_count": summary.negative_count,
        "neutral_count": summary.neutral_count,
        "preferred_product_keys": summary.preferred_product_keys,
        "avoided_product_keys": summary.avoided_product_keys,
        "metadata": summary.metadata,
    }
