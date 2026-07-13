def serialize_stream_event(event):
    return {
        "event": event.event,
        "index": event.index,
        "data": event.data,
    }
