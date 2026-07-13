from urllib.parse import urlparse


class CrawlerFetchPolicy:
    def __init__(self, allowed_domains: list[str] | None = None):
        self.allowed_domains = allowed_domains or ["example.com", "mock.local"]

    def evaluate(self, *, url: str, allow_external_fetch: bool, obey_robots_txt: bool):
        parsed = urlparse(url)
        warnings: list[str] = []

        if parsed.scheme not in ["http", "https", "mock"]:
            return {
                "allowed": False,
                "reason": "UNSUPPORTED_SCHEME",
                "warnings": ["Only http, https, and mock schemes are supported."],
            }

        hostname = parsed.hostname or ""

        if not allow_external_fetch and hostname not in self.allowed_domains:
            return {
                "allowed": False,
                "reason": "EXTERNAL_FETCH_DISABLED",
                "warnings": ["External fetching is disabled by default."],
            }

        if obey_robots_txt:
            warnings.append("ROBOTS_TXT_POLICY_ENABLED")

        return {
            "allowed": True,
            "reason": "ALLOWED",
            "warnings": warnings,
        }
