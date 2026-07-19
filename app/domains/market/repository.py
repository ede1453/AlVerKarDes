from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.market.models import Offer, Price, Store
from app.domains.market.schemas import OfferCreate, PriceSnapshotCreate, StoreCreate


class StoreRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_slug(self, slug: str):
        result = await self.db.execute(
            select(Store).where(Store.slug == slug, Store.deleted_at.is_(None))
        )
        return result.scalar_one_or_none()

    async def create(self, payload: StoreCreate):
        existing = await self.get_by_slug(payload.slug)
        if existing:
            return existing

        data = payload.model_dump()
        data["metadata_json"] = data.pop("metadata", {})
        store = Store(**data)
        self.db.add(store)
        await self.db.commit()
        await self.db.refresh(store)
        return store


class OfferRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_url(self, url: str):
        result = await self.db.execute(
            select(Offer).where(
                Offer.url == url,
                Offer.deleted_at.is_(None),
            )
        )
        return result.scalar_one_or_none()

    async def get_by_id(self, offer_id):
        result = await self.db.execute(
            select(Offer).where(
                Offer.id == offer_id,
                Offer.deleted_at.is_(None),
            )
        )
        return result.scalar_one_or_none()

    async def create(self, payload: OfferCreate):
        existing = await self.get_by_url(payload.url)
        if existing:
            return existing

        data = payload.model_dump()
        data["metadata_json"] = data.pop("metadata", {})
        offer = Offer(**data)
        self.db.add(offer)
        await self.db.commit()
        await self.db.refresh(offer)
        return offer

    async def list_product_ids_with_offers(self, limit: int | None = None):
        # CLIENT-002d: gercek deal-feed'in kaynak taramasi -- hangi
        # urunlerin en az bir gercekten ingest edilmis teklifi var, bunu
        # bulmak icin. is_real_data filtresi burada YAPILMAZ (JSONB alani,
        # bu codebase'in kurulu deseni Python tarafinda filtrelemek --
        # bkz. PriceRepository.list_for_product) -- cagiran taraf
        # (RealDealFeedSourceService) her urun icin gercek teklifleri ayrica
        # filtreliyor.
        stmt = (
            select(Offer.product_id)
            .join(Price, Price.offer_id == Offer.id)
            .where(
                Offer.deleted_at.is_(None),
                Offer.is_active.is_(True),
                Price.deleted_at.is_(None),
            )
            .distinct()
            .order_by(Offer.product_id)
        )

        if limit:
            stmt = stmt.limit(limit)

        result = await self.db.execute(stmt)
        return [row[0] for row in result.all()]

    async def list_for_product_with_store(self, product_id, limit: int | None = None):
        # CLIENT-000b: shopping_pipeline'in arama adimini gercek ingestion'a
        # baglamak icin -- bir urunun gercekten ingest edilmis teklif+magaza
        # cifti. N+1'i onlemek icin Store JOIN edilmis, fiyat ayri sorgulanir
        # (PriceRepository.latest_for_offer, var olan desen).
        stmt = (
            select(Offer, Store)
            .join(Store, Store.id == Offer.store_id)
            .where(
                Offer.product_id == product_id,
                Offer.deleted_at.is_(None),
                Offer.is_active.is_(True),
                Store.deleted_at.is_(None),
            )
            .order_by(Offer.created_at.asc())
        )

        if limit:
            stmt = stmt.limit(limit)

        result = await self.db.execute(stmt)
        return list(result.all())


class PriceRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, payload: PriceSnapshotCreate):
        data = payload.model_dump()
        source = data.pop("source", None)
        observed_at = data.pop("observed_at", None)
        is_real_data = data.pop("is_real_data", True)
        data["metadata_json"] = {
            "source": source,
            "observed_at": observed_at.isoformat() if observed_at else None,
            "is_real_data": is_real_data,
        }
        price = Price(**data)
        self.db.add(price)
        await self.db.commit()
        await self.db.refresh(price)
        return price

    async def list_for_offer(self, offer_id, limit: int | None = None):
        stmt = (
            select(Price)
            .where(
                Price.offer_id == offer_id,
                Price.deleted_at.is_(None),
            )
            .order_by(Price.created_at.asc())
        )

        if limit:
            stmt = stmt.limit(limit)

        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def latest_for_offer(self, offer_id):
        result = await self.db.execute(
            select(Price)
            .where(
                Price.offer_id == offer_id,
                Price.deleted_at.is_(None),
            )
            .order_by(Price.created_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def list_for_product(self, product_id, limit: int | None = None, only_real: bool = False):
        stmt = (
            select(Price)
            .join(Offer, Offer.id == Price.offer_id)
            .where(
                Offer.product_id == product_id,
                Price.deleted_at.is_(None),
                Offer.deleted_at.is_(None),
            )
            .order_by(Price.created_at.asc())
        )

        result = await self.db.execute(stmt)
        prices = list(result.scalars().all())

        if only_real:
            # PARÇA B (bkz. ADR-007): fixture/test-fixture bağlantılardan
            # (is_real_data=false) gelen fiyatlar tüketiciye dönük gerçek
            # fiyat-geçmişi sinyaline hiç karışmamalı -- CONNECT-001/004'te
            # kurulan sızıntı korumasının aynısı, artık yazma noktasında da.
            prices = [
                price for price in prices
                if price.metadata_json.get("is_real_data", True) is not False
            ]

        if limit:
            prices = prices[:limit]

        return prices
