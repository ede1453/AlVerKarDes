from uuid import UUID

from pydantic import Field

from app.shared.base_models import APIModel


class RecommendationRequest(APIModel):
    product_url: str | None = None
    product_name: str | None = None
    offer_id: UUID | None = None
    user_context: dict = Field(default_factory=dict)
