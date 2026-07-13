from app.domains.llm_orchestration.orchestration_service import LLMOrchestrationService
from app.domains.rate_limits.rate_limit_service import RateLimitService


class GuardedLLMOrchestrationService:
    def __init__(
        self,
        orchestration_service: LLMOrchestrationService | None = None,
        rate_limit_service: RateLimitService | None = None,
    ):
        self.orchestration_service = orchestration_service or LLMOrchestrationService()
        self.rate_limit_service = rate_limit_service or RateLimitService()

    def run(self, payload: dict):
        rate_limit = self.rate_limit_service.check(
            {
                "key": payload.get("rate_limit_key", "anonymous"),
                "scope": payload.get("rate_limit_scope", "llm_orchestration"),
            }
        )

        if not rate_limit["allowed"]:
            return {
                "status": "RATE_LIMITED",
                "rate_limit": rate_limit,
                "orchestration": None,
                "metadata": {
                    "guard": "rate_limit",
                    "executed": False,
                },
            }

        orchestration = self.orchestration_service.run(payload)

        return {
            "status": orchestration["status"],
            "rate_limit": rate_limit,
            "orchestration": orchestration,
            "metadata": {
                "guard": "rate_limit",
                "executed": True,
            },
        }

    async def run_with_audit(self, payload: dict):
        rate_limit = self.rate_limit_service.check(
            {
                "key": payload.get("rate_limit_key", "anonymous"),
                "scope": payload.get("rate_limit_scope", "llm_orchestration"),
            }
        )

        if not rate_limit["allowed"]:
            return {
                "status": "RATE_LIMITED",
                "rate_limit": rate_limit,
                "orchestration": None,
                "audit_trace": None,
                "metadata": {
                    "guard": "rate_limit",
                    "executed": False,
                },
            }

        result = await self.orchestration_service.run_with_audit(payload)

        return {
            "status": result["orchestration"]["status"],
            "rate_limit": rate_limit,
            "orchestration": result["orchestration"],
            "audit_trace": result["audit_trace"],
            "metadata": {
                "guard": "rate_limit",
                "executed": True,
            },
        }
