from pydantic import BaseModel, Field


class DecisionSignal(BaseModel):
    type: str
    title: str
    description: str
    weight: float = Field(ge=-1, le=1)
    confidence: float = Field(ge=0, le=100)


class DecisionContract(BaseModel):
    decision: str
    confidence: float = Field(ge=0, le=100)
    positive_signals: list[DecisionSignal] = Field(default_factory=list)
    negative_signals: list[DecisionSignal] = Field(default_factory=list)
    missing_information: list[str] = Field(default_factory=list)
    what_could_change_my_decision: list[str] = Field(default_factory=list)
    uncertainty: dict = Field(default_factory=dict)
    evidence: list[dict] = Field(default_factory=list)
    affiliate_disclosure: dict = Field(default_factory=dict)
