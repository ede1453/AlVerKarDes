from dataclasses import dataclass, field


@dataclass
class LLMOrchestrationRequest:
    preferred_provider: str = "mock"
    fallback_providers: list[str] = field(default_factory=lambda: ["mock"])
    model: str = "mock-shopping-explainer"
    system_prompt: str = ""
    user_prompt: str = ""
    guardrails: list[str] = field(default_factory=list)
    structured_context: dict = field(default_factory=dict)
    max_attempts: int = 2
    prompt_version: str = "shopping_v1"
    timeout_ms: int | None = None


@dataclass
class LLMOrchestrationAttempt:
    provider: str
    status: str
    generated_text: str
    safety_warnings: list[str]
    metadata: dict
    attempt_index: int = 0
    retry_decision: dict | None = None
    timeout_classification: str | None = None


@dataclass
class LLMOrchestrationResult:
    status: str
    selected_provider: str | None
    generated_text: str
    attempts: list[LLMOrchestrationAttempt]
    fallback_used: bool
    prompt_version: str
    metadata: dict
