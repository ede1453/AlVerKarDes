from datetime import timedelta

from app.domains.rate_limits.rate_limit_models import RateLimitCheck, RateLimitRule
from app.domains.rate_limits.rate_limit_store import InMemoryRateLimitStore


class RateLimitEngine:
    DEFAULT_RULES = {
        "llm_gateway": RateLimitRule(scope="llm_gateway", limit=60, window_seconds=60),
        "llm_orchestration": RateLimitRule(scope="llm_orchestration", limit=60, window_seconds=60),
        "observability": RateLimitRule(scope="observability", limit=120, window_seconds=60),
        # CLIENT-002f: password-reset issue -- deliberately strict (industry-
        # typical throttle for "request a reset email" abuse, both probing
        # which emails exist and spamming a real user with reset emails).
        "password_reset": RateLimitRule(scope="password_reset", limit=5, window_seconds=900),
    }

    def __init__(
        self,
        store: InMemoryRateLimitStore | None = None,
        rules: dict[str, RateLimitRule] | None = None,
    ):
        self.store = store or InMemoryRateLimitStore()
        self.rules = rules or dict(self.DEFAULT_RULES)

    def check(self, *, key: str, scope: str) -> RateLimitCheck:
        rule = self.rules.get(scope) or RateLimitRule(
            scope=scope,
            limit=60,
            window_seconds=60,
        )

        usage = self.store.increment(
            key=key,
            scope=scope,
            window_seconds=rule.window_seconds,
        )

        reset_at = usage.window_started_at + timedelta(seconds=rule.window_seconds)
        remaining = max(0, rule.limit - usage.count)
        allowed = usage.count <= rule.limit

        return RateLimitCheck(
            allowed=allowed,
            scope=scope,
            key=key,
            limit=rule.limit,
            remaining=remaining,
            reset_at=reset_at,
            reason="ALLOWED" if allowed else "RATE_LIMIT_EXCEEDED",
        )
