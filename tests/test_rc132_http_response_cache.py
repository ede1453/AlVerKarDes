from app.domains.commerce_ingestion.http_execution import (
    HttpResponse,
    ResponseCache,
)


def test_rc132_response_cache():
    cache = ResponseCache()
    response = HttpResponse(
        status_code=200,
        headers={},
        body="ok",
        elapsed_ms=1,
    )
    cache.set(
        url="https://example.test/feed",
        response=response,
        ttl_seconds=60,
    )
    cached = cache.get(
        "https://example.test/feed"
    )
    assert cached is not None
    assert cached.body == "ok"
