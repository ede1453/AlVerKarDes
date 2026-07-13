from dataclasses import dataclass, field


@dataclass
class LLMGatewayRequest:
    provider: str = "mock"
    model: str = "mock-shopping-explainer"
    system_prompt: str = ""
    user_prompt: str = ""
    guardrails: list[str] = field(default_factory=list)
    structured_context: dict = field(default_factory=dict)
    max_tokens: int = 500
    temperature: float = 0.2
    prompt_version: str = "shopping_v1"


@dataclass
class LLMGatewayResponse:
    provider: str
    model: str
    status: str
    generated_text: str
    safety_warnings: list[str]
    usage: dict
    metadata: dict
