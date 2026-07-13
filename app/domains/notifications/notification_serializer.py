def serialize_notification_message(message):
    return {
        "notification_id": message.notification_id,
        "user_id": message.user_id,
        "channel": message.channel,
        "title": message.title,
        "message": message.message,
        "payload": message.payload,
        "status": message.status,
        "provider": message.provider,
        "provider_response": message.provider_response,
        "metadata": message.metadata,
        "created_at": message.created_at.isoformat(),
    }


def serialize_delivery_result(result):
    return {
        "batch_id": result.batch_id,
        "user_id": result.user_id,
        "requested_channels": result.requested_channels,
        "delivered_count": result.delivered_count,
        "failed_count": result.failed_count,
        "messages": [serialize_notification_message(message) for message in result.messages],
        "metadata": result.metadata,
    }
