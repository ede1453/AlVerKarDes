from app.domains.commerce_ingestion.http_execution import (
    FixtureHttpTransport,
    HttpResponse,
)
from app.domains.commerce_ingestion.production_http import (
    MultiPageConnectorRuntime,
)


def test_rc139_multi_page_runtime():
    page1 = "https://example.test/page/1"
    page2 = "https://example.test/page/2"

    transport = FixtureHttpTransport({
        page1: HttpResponse(
            status_code=200,
            headers={"content-type":"application/json"},
            body='{"items":[{"id":"1"}],"next":"https://example.test/page/2"}',
            elapsed_ms=5,
        ),
        page2: HttpResponse(
            status_code=200,
            headers={"content-type":"application/json"},
            body='{"items":[{"id":"2"}]}',
            elapsed_ms=5,
        ),
    })

    result = MultiPageConnectorRuntime(
        transport
    ).execute(
        start_url=page1,
        max_pages=5,
    )

    assert result["executed"] is True
    assert result["page_count"] == 2
    assert result["item_count"] == 2
