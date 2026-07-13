def serialize_smart_alert(decision):
    return {
        "alert_id": decision.alert_id,
        "user_id": decision.user_id,
        "product_key": decision.product_key,
        "should_alert": decision.should_alert,
        "alert_level": decision.alert_level,
        "alert_score": decision.alert_score,
        "title": decision.title,
        "message": decision.message,
        "channels": decision.channels,
        "reasons": decision.reasons,
        "metadata": decision.metadata,
        "created_at": decision.created_at.isoformat(),
    }
