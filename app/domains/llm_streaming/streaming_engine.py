from app.domains.llm_streaming.streaming_models import (
    LLMStreamEvent,
    LLMStreamingRequest,
)


class LLMStreamingEngine:
    def build_events(self, request: LLMStreamingRequest) -> list[LLMStreamEvent]:
        chunks = self._chunk_text(request.text, request.chunk_size)

        events: list[LLMStreamEvent] = [
            LLMStreamEvent(
                event="start",
                index=0,
                data={
                    "status": "STARTED",
                    "metadata": request.metadata,
                },
            )
        ]

        for index, chunk in enumerate(chunks, start=1):
            events.append(
                LLMStreamEvent(
                    event=request.event_type,
                    index=index,
                    data={
                        "chunk": chunk,
                        "index": index,
                    },
                )
            )

        events.append(
            LLMStreamEvent(
                event="done",
                index=len(events),
                data={
                    "status": "COMPLETED",
                    "chunk_count": len(chunks),
                },
            )
        )

        return events

    def _chunk_text(self, text: str, chunk_size: int) -> list[str]:
        chunk_size = max(1, chunk_size)
        if text == "":
            return []
        return [text[i : i + chunk_size] for i in range(0, len(text), chunk_size)]
