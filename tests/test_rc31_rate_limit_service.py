from app.domains.rate_limits.rate_limit_engine import RateLimitEngine
from app.domains.rate_limits.rate_limit_models import RateLimitRule
from app.domains.rate_limits.rate_limit_service import RateLimitService
from app.domains.rate_limits.rate_limit_store import InMemoryRateLimitStore


def test_rate_limit_service_serializes_check():
    service = RateLimitService(
        RateLimitEngine(
            store=InMemoryRateLimitStore(),
            rules={"test": RateLimitRule(scope="test", limit=1, window_seconds=60)},
        )
    )

    data = service.check({"key": "user-1", "scope": "test"})

    assert data["allowed"] is True
    assert data["scope"] == "test"
    assert data["key"] == "user-1"
    assert "reset_at" in data
