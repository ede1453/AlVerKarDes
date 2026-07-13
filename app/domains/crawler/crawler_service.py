from app.domains.crawler.crawler_models import CrawlResult, create_crawl_id
from app.domains.crawler.crawler_serializer import serialize_crawl_result
from app.domains.crawler.extractor import BasicProductPageExtractor
from app.domains.crawler.fetch_policy import CrawlerFetchPolicy
from app.domains.crawler.mock_fetcher import MockCrawlerFetcher
from app.domains.events.event_bus_service import EventBusService


class CrawlerService:
    def __init__(
        self,
        policy: CrawlerFetchPolicy | None = None,
        fetcher: MockCrawlerFetcher | None = None,
        extractor: BasicProductPageExtractor | None = None,
        event_bus_service: EventBusService | None = None,
    ):
        self.policy = policy or CrawlerFetchPolicy()
        self.fetcher = fetcher or MockCrawlerFetcher()
        self.extractor = extractor or BasicProductPageExtractor()
        self.event_bus_service = event_bus_service or EventBusService()

    def crawl(self, payload: dict):
        policy_result = self.policy.evaluate(
            url=payload["url"],
            allow_external_fetch=payload.get("allow_external_fetch", False),
            obey_robots_txt=payload.get("obey_robots_txt", True),
        )

        warnings = list(policy_result["warnings"])

        if not policy_result["allowed"]:
            result = CrawlResult(
                crawl_id=create_crawl_id(),
                url=payload["url"],
                connector=payload.get("connector", "mock"),
                status=policy_result["reason"],
                allowed=False,
                content_type=None,
                content=None,
                extracted={},
                warnings=warnings,
                metadata={"crawler_version": "crawler_boundary_v1"},
            )
            return self._publish_and_serialize(result)

        fetched = self.fetcher.fetch(
            url=payload["url"],
            timeout_ms=payload.get("timeout_ms", 3000),
        )
        extracted = self.extractor.extract(content=fetched.get("content"), url=payload["url"])

        result = CrawlResult(
            crawl_id=create_crawl_id(),
            url=payload["url"],
            connector=payload.get("connector", "mock"),
            status=fetched["status"],
            allowed=True,
            content_type=fetched.get("content_type"),
            content=fetched.get("content"),
            extracted=extracted,
            warnings=warnings,
            metadata={
                "crawler_version": "crawler_boundary_v1",
                "fetcher_metadata": fetched.get("metadata", {}),
            },
        )

        return self._publish_and_serialize(result)

    def _publish_and_serialize(self, result: CrawlResult):
        serialized = serialize_crawl_result(result)

        self.event_bus_service.publish(
            {
                "event_type": "crawler.crawl_completed",
                "source": "crawler",
                "payload": {
                    "crawl_id": serialized["crawl_id"],
                    "url": serialized["url"],
                    "status": serialized["status"],
                    "allowed": serialized["allowed"],
                },
                "metadata": {"event_version": "event_v1"},
            }
        )

        return serialized
