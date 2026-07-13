from uuid import UUID

from app.domains.deals.deal_summary_service import DealSummaryService
from app.domains.market.service import MarketService


class OfferDealSummaryService:
    def __init__(self, db):
        self.market_service = MarketService(db)
        self.summary_service = DealSummaryService()

    async def summarize_offer(
        self,
        *,
        offer_id: UUID,
        cross_store_min_amount=None,
        store_trust_score=None,
        stock_status: str | None = None,
    ):
        offer = await self.market_service.get_offer(offer_id)

        if not offer:
            raise ValueError("offer_not_found")

        prices = await self.market_service.get_price_history(offer_id)

        effective_stock_status = stock_status
        if effective_stock_status is None and prices:
            latest_price = prices[-1]
            effective_stock_status = getattr(latest_price, "stock_status", None)

        summary = self.summary_service.summarize(
            prices=prices,
            cross_store_min_amount=cross_store_min_amount,
            store_trust_score=store_trust_score,
            stock_status=effective_stock_status or "in_stock",
        )

        return {
            "offer_id": str(offer_id),
            **summary,
        }
