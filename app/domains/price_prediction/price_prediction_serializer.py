def serialize_price_prediction(result):
    return {
        "prediction_id": result.prediction_id,
        "product_key": result.product_key,
        "current_price": result.current_price,
        "predicted_price": result.predicted_price,
        "prediction_horizon_days": result.prediction_horizon_days,
        "direction": result.direction,
        "confidence": result.confidence,
        "recommendation_hint": result.recommendation_hint,
        "reasons": result.reasons,
        "metadata": result.metadata,
        "created_at": result.created_at.isoformat(),
    }
