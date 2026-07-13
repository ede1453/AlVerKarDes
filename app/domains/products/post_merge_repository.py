from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.market.models import Offer
from app.domains.products.models import Product


class PostMergeVerificationRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def count_active_offers_for_product(self, product_id: str) -> int:
        result = await self.db.execute(
            select(func.count())
            .select_from(Offer)
            .where(
                Offer.product_id == product_id,
                Offer.deleted_at.is_(None),
            )
        )
        return int(result.scalar() or 0)

    async def count_active_offers_for_deleted_products(self) -> int:
        result = await self.db.execute(
            select(func.count())
            .select_from(Offer)
            .join(Product, Offer.product_id == Product.id)
            .where(
                Offer.deleted_at.is_(None),
                Product.deleted_at.is_not(None),
            )
        )
        return int(result.scalar() or 0)

    async def count_active_products(self, product_ids: list[str]) -> int:
        if not product_ids:
            return 0

        result = await self.db.execute(
            select(func.count())
            .select_from(Product)
            .where(
                Product.id.in_(product_ids),
                Product.deleted_at.is_(None),
            )
        )
        return int(result.scalar() or 0)
