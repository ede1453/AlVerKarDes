class MockCrawlerFetcher:
    name = "mock"

    def fetch(self, *, url: str, timeout_ms: int):
        return {
            "status": "FETCHED",
            "content_type": "text/html",
            "content": (
                "<html><body>"
                "<h1>MacBook Air Mock Offer</h1>"
                "<span class='price'>949.00</span>"
                "<span class='currency'>EUR</span>"
                "</body></html>"
            ),
            "metadata": {
                "fetcher": self.name,
                "timeout_ms": timeout_ms,
                "external": False,
            },
        }
