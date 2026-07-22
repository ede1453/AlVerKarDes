from datetime import timedelta
from typing import Any

from app.domains.rate_limits.rate_limit_models import RateLimitCheck, RateLimitRule
from app.domains.rate_limits.rate_limit_store_factory import get_rate_limit_store


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
        store: Any | None = None,
        rules: dict[str, RateLimitRule] | None = None,
    ):
        # SCALE-001: get_rate_limit_store() is env-driven (AICI_CACHE_BACKEND,
        # same switch the cache backend already uses) -- defaults to
        # InMemoryRateLimitStore only when redis isn't configured (e.g. bare
        # unit tests). Both stores implement the same
        # increment(key, scope, window_seconds) -> RateLimitUsage contract.
        self.store = store or get_rate_limit_store()
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
