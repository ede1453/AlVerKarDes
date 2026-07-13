from datetime import datetime, timezone

from app.domains.commerce_ingestion.http_execution import (
    DomainRateLimiter,
    RobotsPolicyService,
)


def test_rc131_robots_disallow():
    service = RobotsPolicyService()
    service.set_policy(
        domain="example.test",
        allowed_paths=["/"],
        disallowed_paths=["/private"],
    )
    assert service.evaluate(
        "https://example.test/private/data"
    )["allowed"] is False

def test_rc131_rate_limiter():
    limiter = DomainRateLimiter()
    now = datetime.now(timezone.utc)
    assert limiter.check(
        domain="example.test",
        minimum_interval_seconds=10,
        at_time=now,
    )["allowed"] is True
    second = limiter.check(
        domain="example.test",
        minimum_interval_seconds=10,
        at_time=now,
    )
    assert second["allowed"] is False
