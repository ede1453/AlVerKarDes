from datetime import datetime, timezone

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.market.models import Offer
from app.domains.products.models import Product


class ProductMergeRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_product(self, product_id):
        result = await self.db.execute(
            select(Product).where(
                Product.id == product_id,
                Product.deleted_at.is_(None),
            )
        )
        return result.scalar_one_or_none()

    async def reassign_offers(self, *, from_product_id, to_product_id) -> int:
        result = await self.db.execute(
            update(Offer)
            .where(
                Offer.product_id == from_product_id,
                Offer.deleted_at.is_(None),
            )
            .values(product_id=to_product_id)
        )
        return int(result.rowcount or 0)

    async def soft_delete_product(self, product_id) -> bool:
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

    async def rollback(self):
        await self.db.rollback()
