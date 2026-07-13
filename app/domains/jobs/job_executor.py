from app.domains.llm_orchestration.orchestration_service import LLMOrchestrationService


class JobExecutor:
    def __init__(self, orchestration_service: LLMOrchestrationService | None = None):
        self.orchestration_service = orchestration_service or LLMOrchestrationService()

    def execute(self, *, job_type: str, payload: dict) -> dict:
        if job_type == "llm_orchestration":
            return self.orchestration_service.run(payload)

        if job_type == "noop":
            return {"status": "COMPLETED", "echo": payload}

        raise ValueError(f"Unsupported job_type: {job_type}")
