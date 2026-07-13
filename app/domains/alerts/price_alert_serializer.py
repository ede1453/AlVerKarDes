def serialize_price_alert_decisions(decisions):
    return [
        {
            "should_notify": item.should_notify,
            "alert_type": item.alert_type,
            "reasons": item.reasons,
            "data": item.data,
        }
        for item in decisions
    ]
