from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel


class DealSummaryPriceInput(BaseModel):
    amount: Decimal
    observed_at: datetime


class DealSummaryRequest(BaseModel):
    prices: list[DealSummaryPriceInput]
    cross_store_min_amount: Decimal | None = None
    store_trust_score: float | None = None
    stock_status: str | None = "in_stock"


class DealSummaryResponse(BaseModel):
    has_price_data: bool
    lowest_prices: dict
    deal_score: dict | None
    recommendation: str
    message: str
