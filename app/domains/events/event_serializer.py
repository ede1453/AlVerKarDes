def serialize_event(event):
    return {
        "id": event.id,
        "event_type": event.event_type,
        "source": event.source,
        "payload": event.payload,
        "metadata": event.metadata,
        "status": event.status,
        "created_at": event.created_at.isoformat(),
    }
