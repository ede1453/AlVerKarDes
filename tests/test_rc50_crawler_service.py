from app.domains.crawler.crawler_service import CrawlerService
from app.domains.events.event_repository_factory import reset_event_repository


def test_crawler_service_mock_crawl_emits_event():
    reset_event_repository()
    service = CrawlerService()

    result = service.crawl({"url": "https://example.com/product"})

    assert result["status"] == "FETCHED"
    assert result["allowed"] is True
    assert result["extracted"]["product_name"] == "MacBook Air Mock Offer"

    events = service.event_bus_service.list_recent({"event_type": "crawler.crawl_completed", "source": "crawler"})
    assert events


def test_crawler_service_blocks_external_by_default():
    service = CrawlerService()

    result = service.crawl({"url": "https://amazon.de/product"})

    assert result["allowed"] is False
    assert result["status"] == "EXTERNAL_FETCH_DISABLED"
