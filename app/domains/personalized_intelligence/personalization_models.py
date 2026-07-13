from dataclasses import dataclass, field


@dataclass
class UserPreferenceProfile:
    user_id: str
    preferred_brands: list[str] = field(default_factory=list)
    avoided_brands: list[str] = field(default_factory=list)
    preferred_categories: list[str] = field(default_factory=list)
    price_sensitivity: str = "MEDIUM"
    minimum_confidence: int = 70


@dataclass
class PersonalizedDecisionInput:
    user_id: str
    final_decision: str
    confidence: int
    product_brand: str | None = None
    product_category: str | None = None
    current_price: str | None = None
    risk_level: str | None = None
    opportunity_level: str | None = None
    reason_codes: list[str] = field(default_factory=list)


@dataclass
class PersonalizedDecisionResult:
    user_id: str
    base_decision: str
    personalized_decision: str
    personalized_confidence: int
    personalization_reasons: list[str]
    user_profile_snapshot: dict
