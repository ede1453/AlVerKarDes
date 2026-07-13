from app.domains.rate_limits.rate_limit_engine import RateLimitEngine
from app.domains.rate_limits.rate_limit_serializer import serialize_rate_limit_check


class RateLimitService:
    def __init__(self, engine: RateLimitEngine | None = None):
        self.engine = engine or RateLimitEngine()

    def check(self, payload: dict):
        check = self.engine.check(
            key=payload.get("key", "anonymous"),
            scope=payload.get("scope", "llm_gateway"),
        )

        return serialize_rate_limit_check(check)
