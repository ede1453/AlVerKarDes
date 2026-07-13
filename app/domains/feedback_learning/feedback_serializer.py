def serialize_feedback(record):
    return {
        "id": record.id,
        "user_id": record.user_id,
        "decision_id": record.decision_id,
        "product_id": record.product_id,
        "offer_id": record.offer_id,
        "feedback_type": record.feedback_type,
        "rating": record.rating,
        "comment": record.comment,
        "metadata": record.metadata,
        "created_at": record.created_at.isoformat(),
    }


def serialize_feedback_learning_summary(summary):
    return {
        "total_feedback_count": summary.total_feedback_count,
        "helpful_count": summary.helpful_count,
        "not_helpful_count": summary.not_helpful_count,
        "purchased_count": summary.purchased_count,
        "ignored_count": summary.ignored_count,
        "average_rating": summary.average_rating,
        "learning_signal": summary.learning_signal,
        "confidence_adjustment": summary.confidence_adjustment,
        "reason_codes": summary.reason_codes,
    }
