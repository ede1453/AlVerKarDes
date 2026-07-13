from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.market.models import Offer
from app.domains.products.models import Product


class MasterProductRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_active_product_ids_by_offer_urls(self, urls: list[str]) -> list[dict]:
        if not urls:
            return []

        result = await self.db.execute(
            select(
                Offer.product_id,
                func.count(Offer.id).label("offer_count"),
                Product.canonical_key,
            )
            .join(Product, Offer.product_id == Product.id)
            .where(
                Offer.url.in_(urls),
                Offer.deleted_at.is_(None),
                Product.deleted_at.is_(None),
            )
            .group_by(Offer.product_id, Product.canonical_key)
        )

        return [
            {
                "product_id": row.product_id,
                "offer_count": int(row.offer_count or 0),
                "canonical_key": row.canonical_key,
                "canonical_quality": self._canonical_quality(row.canonical_key),
            }
            for row in result.all()
        ]

    def _canonical_quality(self, canonical_key: str | None) -> int:
        if not canonical_key:
            return 0
        score = len(canonical_key.split("::"))
        score += 5 if "macbook-air" in canonical_key else 0
        score += 3 if "16gb" in canonical_key else 0
        score += 3 if "512gb" in canonical_key else 0
        return score
