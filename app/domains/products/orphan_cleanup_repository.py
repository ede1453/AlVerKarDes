from datetime import datetime, timezone

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.market.models import Offer
from app.domains.products.models import Product


class OrphanProductCleanupRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_active_product_ids_without_active_offers(self) -> list[str]:
        active_offer_exists = (
            select(Offer.id)
            .where(
                Offer.product_id == Product.id,
                Offer.deleted_at.is_(None),
            )
            .exists()
        )

        result = await self.db.execute(
            select(Product.id)
            .where(
                Product.deleted_at.is_(None),
                ~active_offer_exists,
            )
        )

        return [str(item) for item in result.scalars().all()]

    async def soft_delete_product(self, product_id: str) -> bool:
        result = await self.db.execute(
            update(Product)
            .where(
                Product.id == product_id,
                Product.deleted_at.is_(None),
            )
            .values(deleted_at=datetime.now(timezone.utc))
        )
        return bool(result.rowcount)

    async def commit(self):
        await self.db.commit()
