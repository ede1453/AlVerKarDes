def serialize_deal_detection_result(result):
    return {
        "deal_id": result.deal_id,
        "product_key": result.product_key,
        "offer": result.offer,
        "deal_level": result.deal_level,
        "deal_score": result.deal_score,
        "price_signal": result.price_signal,
        "personalization_signal": result.personalization_signal,
        "confidence": result.confidence,
        "reasons": result.reasons,
        "next_actions": result.next_actions,
        "metadata": result.metadata,
        "created_at": result.created_at.isoformat(),
    }
