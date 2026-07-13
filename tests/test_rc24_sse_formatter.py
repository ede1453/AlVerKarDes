from app.domains.llm_streaming.sse_formatter import SSEFormatter


def test_sse_formatter_outputs_event_stream_format():
    text = SSEFormatter().format(
        event="token",
        data={"chunk": "hello", "index": 1},
    )

    assert text.startswith("event: token\n")
    assert '"chunk": "hello"' in text
    assert text.endswith("\n\n")
