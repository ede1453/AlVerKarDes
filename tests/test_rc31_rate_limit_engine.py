from app.domains.rate_limits.rate_limit_engine import RateLimitEngine
from app.domains.rate_limits.rate_limit_models import RateLimitRule
from app.domains.rate_limits.rate_limit_store import InMemoryRateLimitStore


def test_rate_limit_engine_allows_within_limit():
    engine = RateLimitEngine(
        store=InMemoryRateLimitStore(),
        rules={"test": RateLimitRule(scope="test", limit=2, window_seconds=60)},
    )

    first = engine.check(key="user-1", scope="test")
    second = engine.check(key="user-1", scope="test")

    assert first.allowed is True
    assert second.allowed is True
    assert second.remaining == 0


def test_rate_limit_engine_blocks_after_limit():
    engine = RateLimitEngine(
        store=InMemoryRateLimitStore(),
        rules={"test": RateLimitRule(scope="test", limit=1, window_seconds=60)},
    )

    first = engine.check(key="user-1", scope="test")
    second = engine.check(key="user-1", scope="test")

    assert first.allowed is True
    assert second.allowed is False
    assert second.reason == "RATE_LIMIT_EXCEEDED"
