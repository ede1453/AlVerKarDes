from app.domains.llm_streaming.sse_formatter import SSEFormatter
from app.domains.llm_streaming.streaming_engine import LLMStreamingEngine
from app.domains.llm_streaming.streaming_models import LLMStreamingRequest
from app.domains.llm_streaming.streaming_serializer import serialize_stream_event


class LLMStreamingService:
    def __init__(
        self,
        engine: LLMStreamingEngine | None = None,
        formatter: SSEFormatter | None = None,
    ):
        self.engine = engine or LLMStreamingEngine()
        self.formatter = formatter or SSEFormatter()

    def preview(self, payload: dict):
        events = self.engine.build_events(
            LLMStreamingRequest(
                text=payload.get("text", ""),
                event_type=payload.get("event_type", "token"),
                chunk_size=payload.get("chunk_size", 24),
                metadata=payload.get("metadata", {}),
            )
        )

        return {
            "events": [serialize_stream_event(event) for event in events],
            "event_count": len(events),
        }

    def sse_lines(self, payload: dict):
        events = self.preview(payload)["events"]

        for event in events:
            yield self.formatter.format(
                event=event["event"],
                data={
                    "index": event["index"],
                    **event["data"],
                },
            )
