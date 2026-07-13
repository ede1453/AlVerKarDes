from pydantic import BaseModel


class OfferDealSummaryResponse(BaseModel):
    offer_id: str
    has_price_data: bool
    lowest_prices: dict
    deal_score: dict | None
    recommendation: str
    message: str
