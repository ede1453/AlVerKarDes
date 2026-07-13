from app.domains.commerce_ingestion.production_http import (
    PaginationService,
)


def test_rc138_payload_pagination():
    service = PaginationService()
    assert service.get_next_url(
        payload={
            "pagination":{
                "next":"https://example.test/page/2"
            }
        },
        headers={},
    ) == "https://example.test/page/2"

def test_rc138_link_header_pagination():
    service = PaginationService()
    result = service.get_next_url(
        payload={},
        headers={
            "link": '<https://example.test/page/2>; rel="next"'
        },
    )
    assert result == "https://example.test/page/2"