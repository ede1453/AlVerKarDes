from app.domains.llm_streaming.streaming_service import LLMStreamingService


def test_streaming_service_preview_serializes_events():
    data = LLMStreamingService().preview(
        {
            "text": "abcdef",
            "chunk_size": 3,
            "metadata": {"provider": "mock"},
        }
    )

    assert data["event_count"] == 4
    assert data["events"][0]["event"] == "start"
    assert data["events"][1]["data"]["chunk"] == "abc"


def test_streaming_service_sse_lines_yields_formatted_events():
    lines = list(
        LLMStreamingService().sse_lines(
            {
                "text": "abcd",
                "chunk_size": 2,
            }
        )
    )

    assert lines[0].startswith("event: start")
    assert any("event: done" in line for line in lines)
