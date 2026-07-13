from app.domains.commerce_ingestion.http_execution import (
    FixtureHttpTransport,
    HttpConnectorExecutionService,
    HttpResponse,
)


def test_rc130_http_execution():
    url = "https://example.test/feed"
    transport = FixtureHttpTransport({
        url: HttpResponse(
            status_code=200,
            headers={"content-type":"application/json"},
            body='{"items":[]}',
            elapsed_ms=25,
        )
    })
    service = HttpConnectorExecutionService(transport)
    service.robots.set_policy(
        domain="example.test",
        allowed_paths=["/feed"],
    )
    result = service.execute(
        connector_id="example",
        url=url,
    )
    assert result["executed"] is True
    assert result["response"]["status_code"] == 200
