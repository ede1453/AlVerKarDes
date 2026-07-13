from dataclasses import dataclass, field


@dataclass
class ExplanationInput:
    final_decision: str
    confidence: int
    risk_level: str | None = None
    opportunity_level: str | None = None
    reason_codes: list[str] = field(default_factory=list)
    explanation: list[str] = field(default_factory=list)
    scores: dict = field(default_factory=dict)
    market: dict = field(default_factory=dict)


@dataclass
class ExplanationResult:
    headline: str
    summary: str
    reason_tree: list[dict]
    confidence_breakdown: dict
    risk_breakdown: dict
    opportunity_breakdown: dict
    llm_prompt_context: dict
