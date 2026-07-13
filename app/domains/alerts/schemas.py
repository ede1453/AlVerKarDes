from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel


class AlertRuleCreate(BaseModel):
    user_id: UUID
    offer_id: UUID
    rule_type: str
    target_amount: Decimal | None = None
    drop_percent_threshold: Decimal | None = None
    notify_on_back_in_stock: bool = False


class AlertRuleRead(BaseModel):
    id: UUID
    user_id: UUID
    offer_id: UUID
    rule_type: str
    target_amount: Decimal | None = None
    drop_percent_threshold: Decimal | None = None
    notify_on_back_in_stock: bool
    is_active: bool

    model_config = {"from_attributes": True}
