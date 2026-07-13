from app.domains.crawler.fetch_policy import CrawlerFetchPolicy


def test_crawler_policy_blocks_external_fetch_by_default():
    result = CrawlerFetchPolicy().evaluate(
        url="https://amazon.de/item",
        allow_external_fetch=False,
        obey_robots_txt=True,
    )

    assert result["allowed"] is False
    assert result["reason"] == "EXTERNAL_FETCH_DISABLED"


def test_crawler_policy_allows_allowed_domain():
    result = CrawlerFetchPolicy().evaluate(
        url="https://example.com/item",
        allow_external_fetch=False,
        obey_robots_txt=True,
    )

    assert result["allowed"] is True
    assert "ROBOTS_TXT_POLICY_ENABLED" in result["warnings"]
