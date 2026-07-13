from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.market.price_change_detector import PriceChangeDetector
from app.domains.market.price_dedup import PriceSnapshotDeduplicator
from app.domains.market.repository import OfferRepository, PriceRepository, StoreRepository
from app.domains.market.schemas import OfferCreate, PriceSnapshotCreate, StoreCreate


class MarketService:
    def __init__(self, db: AsyncSession):
        self.store_repo = StoreRepository(db)
        self.offer_repo = OfferRepository(db)
        self.price_repo = PriceRepository(db)

    async def create_store(self, payload: StoreCreate):
        return await self.store_repo.create(payload)

    async def create_offer(self, payload: OfferCreate):
        return await self.offer_repo.create(payload)

    async def get_or_create_offer(self, payload: OfferCreate):
        existing = await self.offer_repo.get_by_url(payload.url)
        if existing:
            return existing, False

        offer = await self.offer_repo.create(payload)
        return offer, True

    async def save_price_snapshot(self, payload: PriceSnapshotCreate):
        latest_price = await self.get_latest_price_point(payload.offer_id)

        decision = PriceSnapshotDeduplicator().should_create_snapshot(
            latest_price=latest_price,
            new_amount=payload.amount,
            new_currency=payload.currency,
            new_stock_status=payload.stock_status,
        )

        if not decision.should_create:
            latest_price._price_created = False
            latest_price._price_dedup_reason = decision.reason
            latest_price._price_change = PriceChangeDetector().detect(previous_price=latest_price, current_price=latest_price)
            return latest_price

        price = await self.price_repo.create(payload)
        price._price_created = True
        price._price_dedup_reason = decision.reason
        price._price_change = PriceChangeDetector().detect(previous_price=latest_price, current_price=price)
        return price

    async def get_latest_price_point(self, offer_id):
        return await self.price_repo.latest_for_offer(offer_id)

    async def get_latest_price(self, offer_id):
        return await self.get_latest_price_point(offer_id)

    async def get_price_history(self, offer_id, limit: int | None = None):
        return await self.price_repo.list_for_offer(offer_id, limit=limit)

    async def get_prices_for_offer(self, offer_id, limit: int | None = None):
        return await self.get_price_history(offer_id, limit=limit)

    async def get_offer(self, offer_id):
        return await self.offer_repo.get_by_id(offer_id)

    async def get_price_points_for_offer(self, offer_id, limit: int | None = None):
        return await self.get_price_history(offer_id, limit=limit)