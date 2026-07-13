from app.domains.commerce_ingestion.production_http import (
    ConditionalRequestState,
)


def test_rc136_conditional_request_headers():
    state = ConditionalRequestState()
    state.update(
        url="https://example.test/feed",
        headers={
            "ETag":"abc123",
            "Last-Modified":"Mon, 01 Jan 2026 00:00:00 GMT",
        },
    )
    headers = state.build_headers(
        "https://example.test/feed"
    )
    assert headers["If-None-Match"] == "abc123"
    assert "If-Modified-Since" in headers
