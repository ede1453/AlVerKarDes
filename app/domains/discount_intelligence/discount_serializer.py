def serialize_discount_result(result):
    return {
        "discount_id": result.discount_id,
        "product_key": result.product_key,
        "current_price": result.current_price,
        "claimed_original_price": result.claimed_original_price,
        "effective_discount_percent": result.effective_discount_percent,
        "discount_quality": result.discount_quality,
        "fake_discount_risk": result.fake_discount_risk,
        "confidence": result.confidence,
        "reasons": result.reasons,
        "metadata": result.metadata,
        "created_at": result.created_at.isoformat(),
    }
