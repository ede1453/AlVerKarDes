from pydantic import BaseModel, Field


class EvidenceItem(BaseModel):
    type: str
    title: str
    summary: str | None = None
    source_name: str | None = None
    source_url: str | None = None
    confidence: float = Field(ge=0, le=100)
    data: dict = Field(default_factory=dict)


class EvidenceBundle(BaseModel):
    items: list[EvidenceItem] = Field(default_factory=list)

    def add(self, item: EvidenceItem) -> None:
        self.items.append(item)

    def by_type(self, evidence_type: str) -> list[EvidenceItem]:
        return [item for item in self.items if item.type == evidence_type]
