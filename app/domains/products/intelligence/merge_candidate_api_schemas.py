from pydantic import BaseModel


class MergeCandidateOfferInput(BaseModel):
    source: str
    title: str
    url: str | None = None
    gtin: str | None = None
    ean: str | None = None
    mpn: str | None = None
    sku: str | None = None


class MergeCandidateRequest(BaseModel):
    country: str = "DE"
    offers: list[MergeCandidateOfferInput]


class MergeCandidateRead(BaseModel):
    signature: str
    master_title: str
    offer_count: int
    average_confidence: float
    decision: str
    offer_titles: list[str]
    sources: list[str]


class MergeCandidateResponse(BaseModel):
    country: str
    input_offer_count: int
    candidate_count: int
    candidates: list[MergeCandidateRead]
