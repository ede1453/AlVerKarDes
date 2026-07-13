from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.market.models import Offer
from app.domains.products.models import Product


class DuplicateProductRegressionRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def count_active_products(self) -> int:
        result = await self.db.execute(
            select(func.count())
            .select_from(Product)
            .where(Product.deleted_at.is_(None))
        )
        return int(result.scalar() or 0)

    async def count_deleted_products(self) -> int:
        result = await self.db.execute(
            select(func.count())
            .select_from(Product)
            .where(Product.deleted_at.is_not(None))
        )
        return int(result.scalar() or 0)

    async def count_distinct_active_offer_products(self) -> int:
        result = await self.db.execute(
            select(func.count(func.distinct(Offer.product_id)))
            .select_from(Offer)
            .join(Product, Offer.product_id == Product.id)
            .where(
                Offer.deleted_at.is_(None),
                Product.deleted_at.is_(None),
            )
        )
        return int(result.scalar() or 0)
