from uuid import UUID

from pydantic import BaseModel


class MergeCandidateReviewRequest(BaseModel):
    status: str


class MergeCandidateReviewResponse(BaseModel):
    id: UUID
    signature: str
    decision: str
    status: str

    model_config = {"from_attributes": True}
