from dataclasses import dataclass, field


@dataclass
class LLMExplanationInput:
    assistant_decision: str
    headline: str
    summary: str
    confidence: int
    risk_level: str | None = None
    opportunity_level: str | None = None
    next_actions: list[str] = field(default_factory=list)
    reason_codes: list[str] = field(default_factory=list)
    explanation: list[str] = field(default_factory=list)
    assistant_context: dict = field(default_factory=dict)
    language: str = "en"
    tone: str = "clear"
    prompt_version: str = "shopping_v1"


@dataclass
class LLMExplanationPrompt:
    system_prompt: str
    user_prompt: str
    guardrails: list[str]
    structured_context: dict
    prompt_version: str = "shopping_v1"


@dataclass
class LLMExplanationDraft:
    mode: str
    language: str
    tone: str
    explanation_text: str
    prompt: LLMExplanationPrompt
    prompt_version: str = "shopping_v1"
