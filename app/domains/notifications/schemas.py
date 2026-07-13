from uuid import UUID

from pydantic import BaseModel


class PendingNotificationCreate(BaseModel):
    user_id: UUID
    offer_id: UUID
    rule_id: UUID
    channel: str = "IN_APP"
    title: str
    message: str


class PendingNotificationRead(BaseModel):
    id: UUID
    user_id: UUID
    offer_id: UUID
    rule_id: UUID
    channel: str
    status: str
    title: str
    message: str

    model_config = {"from_attributes": True}
