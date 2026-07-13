from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.market.models import Offer
from app.domains.products.models import Product


class DataIntegrityRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

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

    async def count_duplicate_active_canonical_keys(self) -> int:
        subquery = (
            select(Product.canonical_key)
            .where(
                Product.deleted_at.is_(None),
                Product.canonical_key.is_not(None),
            )
            .group_by(Product.canonical_key)
            .having(func.count(Product.id) > 1)
            .subquery()
        )

        result = await self.db.execute(
            select(func.count()).select_from(subquery)
        )
        return int(result.scalar() or 0)
