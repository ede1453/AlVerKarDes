from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import uuid4


@dataclass
class AIExplanationResult:
    explanation_id: str
    mode: str
    language: str
    tone: str
    headline: str
    explanation_text: str
    bullet_points: list[str]
    risk_notes: list[str]
    next_actions: list[str]
    source_signals: dict
    metadata: dict = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


def create_explanation_id() -> str:
    return str(uuid4())
