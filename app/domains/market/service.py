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

    async def get_price_history_for_product(self, product_id, limit: int | None = None, only_real: bool = True):
        return await self.price_repo.list_for_product(product_id, limit=limit, only_real=only_real)

    async def get_price_history_summary_for_product(self, product_id) -> dict:
        # CLIENT-002b: shopping_pipeline_service._real_price_history()'nin
        # ozet-hesaplama mantigi buraya tasindi (paylasilan tek kaynak) --
        # CLIENT-002b'nin GET /products/{id}/detail'i de ayni gercek
        # market.Price verisinden ayni sekilde ozet uretsin diye, ikinci bir
        # paralel implementasyon (bu projenin tekrar tekrar bulup duzelttigi
        # bir hata sinifi -- bkz. Marketplace-Product-Paralel-Implementasyon)
        # yaratmadan. Davranis birebir korundu (CONNECT-001'in canli
        # dogrulanmis mantigi), sadece canonical_key -> product lookup'i
        # cagiran tarafta (pipeline_service) kaldi.
        price_points = await self.get_price_history_for_product(product_id)
        if not price_points:
            return {"status": "INSUFFICIENT_DATA", "reason": "NO_PRICE_HISTORY"}

        amounts = [float(point.amount) for point in price_points]
        latest = amounts[-1]
        if len(amounts) > 1 and amounts[-1] < amounts[0]:
            trend = "DOWN"
        elif len(amounts) > 1 and amounts[-1] > amounts[0]:
            trend = "UP"
        else:
            trend = "FLAT"

        return {
            "status": "OK",
            "latest_price": f"{latest:.2f}",
            "min_price": f"{min(amounts):.2f}",
            "average_price": f"{(sum(amounts) / len(amounts)):.2f}",
            "max_price": f"{max(amounts):.2f}",
            "trend": trend,
            "points": [{"price": f"{amount:.2f}"} for amount in amounts],
        }

    async def get_offers_with_latest_price_for_product(self, product_id, limit: int | None = None):
        # CLIENT-000b: shopping_pipeline'in arama adiminin (ve
        # GET /market/products/{id}/offers'in) tek gercek veri kaynagi --
        # gercekten ingest edilmis teklif+magaza+en-son-fiyat ucluleri.
        # Fixture-mode connector verisi de dahil (is_real_data alaninda
        # aciklaniyor) -- bu "hangi teklifler var" sorusu, deal-detection'in
        # "hangi fiyat GERCEKTEN guvenilir" sorusundan (only_real=True,
        # get_price_history_for_product) farkli, o filtre burada YOK.
        pairs = await self.offer_repo.list_for_product_with_store(product_id, limit=limit)
        results = []
        for offer, store in pairs:
            price = await self.price_repo.latest_for_offer(offer.id)
            if price is None:
                continue
            results.append({"offer": offer, "store": store, "price": price})
        return results