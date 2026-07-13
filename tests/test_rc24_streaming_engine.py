from app.domains.llm_streaming.streaming_engine import LLMStreamingEngine
from app.domains.llm_streaming.streaming_models import LLMStreamingRequest


def test_streaming_engine_builds_start_token_done_events():
    events = LLMStreamingEngine().build_events(
        LLMStreamingRequest(
            text="abcdef",
            chunk_size=2,
            metadata={"source": "test"},
        )
    )

    assert [event.event for event in events] == ["start", "token", "token", "token", "done"]
    assert events[1].data["chunk"] == "ab"
    assert events[-1].data["chunk_count"] == 3


def test_streaming_engine_handles_empty_text():
    events = LLMStreamingEngine().build_events(
        LLMStreamingRequest(text="", chunk_size=2)
    )

    assert [event.event for event in events] == ["start", "done"]
    assert events[-1].data["chunk_count"] == 0
