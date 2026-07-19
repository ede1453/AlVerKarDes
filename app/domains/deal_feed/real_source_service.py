from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.deals.offer_deal_summary_service import OfferDealSummaryService
from app.domains.market.service import MarketService
from app.domains.products.service import ProductService


class RealDealFeedSourceService:
    """CLIENT-002d: bridges the deal-feed algorithm (DealFeedBuilder --
    dedup/personalization scoring, unchanged, still unit-tested in
    tests/test_rc205_deal_feed_service.py) to REAL ingested data, the same
    way CLIENT-000b bridged shopping_pipeline's search step and CLIENT-002b
    bridged the product detail endpoint. Does not touch DealFeedService's
    in-memory ingest_deals()/_deals -- that path stays as-is (still
    independently unit-tested), this is a separate, request-scoped read
    path over market.Price/Offer/Product.

    Deliberately excludes any offer whose latest price is NOT
    is_real_data=True (same discipline as
    MarketService.get_price_history_for_product(only_real=True)) -- a
    fixture-mode connector's parked data (e.g. Amazon, is_real_data:
    false) must never surface in a feed presented to users as "real
    deals". See WIKI_ROOT 07-Issues-Risks/Deal-Feed-Kopuk-Veri-Kaynagi-CLIENT-002b.
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        self.product_service = ProductService(db)
        self.market_service = MarketService(db)
        self.deal_summary_service = OfferDealSummaryService(db)

    async def list_real_deals(self, limit: int = 100) -> list[dict]:
        product_ids = await self.market_service.list_product_ids_with_offers(limit=limit)

        deals: list[dict] = []
        for product_id in product_ids:
            product = await self.product_service.get_by_id(product_id)
            if product is None:
                continue

            pairs = await self.market_service.get_offers_with_latest_price_for_product(product_id)
            real_pairs = [
                item for item in pairs
                if item["price"].metadata_json.get("is_real_data", True) is not False
            ]
            if not real_pairs:
                continue

            cheapest = min(real_pairs, key=lambda item: item["price"].amount)

            try:
                summary = await self.deal_summary_service.summarize_offer(offer_id=cheapest["offer"].id)
            except ValueError:
                continue

            if not summary.get("has_price_data"):
                continue

            deal_score = summary.get("deal_score") or {}

            deals.append(
                {
                    "canonical_product_key": product.canonical_key,
                    "product_id": str(product.id),
                    "product_name": product.title,
                    "offer_id": str(cheapest["offer"].id),
                    "source_id": cheapest["store"].name,
                    "marketplace": cheapest["store"].name,
                    "price": float(cheapest["price"].amount),
                    "effective_price": float(cheapest["price"].amount),
                    "currency": cheapest["price"].currency,
                    "confidence_score": deal_score.get("score", 0),
                    "opportunity_score": deal_score.get("score", 0),
                    "observed_discount_pct": 0,
                    "deal_decision": deal_score.get("decision"),
                    "deal_message": summary.get("message"),
                    "is_real_data": True,
                }
            )

        return deals
