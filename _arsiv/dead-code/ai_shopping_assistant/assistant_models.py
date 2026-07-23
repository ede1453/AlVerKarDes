from dataclasses import dataclass, field


@dataclass
class ShoppingAssistantInput:
    user_id: str | None = None
    query: str | None = None
    product_name: str | None = None
    product_brand: str | None = None
    product_category: str | None = None
    current_price: str | None = None
    currency: str = "EUR"
    final_decision: str = "WATCH"
    confidence: int = 70
    risk_level: str | None = None
    opportunity_level: str | None = None
    reason_codes: list[str] = field(default_factory=list)
    explanation: list[str] = field(default_factory=list)
    personalized_decision: str | None = None
    personalized_confidence: int | None = None
    personalization_reasons: list[str] = field(default_factory=list)
    trust_score: int | None = None
    community_score: int | None = None
    metadata: dict = field(default_factory=dict)


@dataclass
class ShoppingAssistantAdvice:
    assistant_decision: str
    headline: str
    summary: str
    confidence: int
    risk_level: str | None
    opportunity_level: str | None
    next_actions: list[str]
    reason_codes: list[str]
    explanation: list[str]
    assistant_context: dict
