from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.products.models import Brand, Category, Product
from app.domains.products.schemas import BrandCreate, CategoryCreate, ProductCreate


class BrandRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, payload: BrandCreate):
        result = await self.db.execute(
            select(Brand).where(Brand.slug == payload.slug, Brand.deleted_at.is_(None))
        )
        existing = result.scalar_one_or_none()
        if existing:
            return existing

        data = payload.model_dump()
        data["metadata_json"] = {}
        brand = Brand(**data)
        self.db.add(brand)
        await self.db.commit()
        await self.db.refresh(brand)
        return brand


class CategoryRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, payload: CategoryCreate):
        result = await self.db.execute(
            select(Category).where(Category.slug == payload.slug, Category.deleted_at.is_(None))
        )
        existing = result.scalar_one_or_none()
        if existing:
            return existing

        category = Category(**payload.model_dump(), metadata_json={})
        self.db.add(category)
        await self.db.commit()
        await self.db.refresh(category)
        return category


class ProductRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_canonical_key(self, key: str):
        result = await self.db.execute(
            select(Product).where(
                Product.canonical_key == key,
                Product.deleted_at.is_(None),
            )
        )
        return result.scalar_one_or_none()

    async def get_by_id(self, product_id):
        result = await self.db.execute(
            select(Product).where(
                Product.id == product_id,
                Product.deleted_at.is_(None),
            )
        )
        return result.scalar_one_or_none()

    async def create(self, payload: ProductCreate):
        if payload.canonical_key:
            existing = await self.get_by_canonical_key(payload.canonical_key)
            if existing:
                return existing

        data = payload.model_dump()
        data["metadata_json"] = data.pop("metadata", {})
        product = Product(**data)
        self.db.add(product)
        await self.db.commit()
        await self.db.refresh(product)
        return product

    async def search(self, query: str, limit: int = 20):
        search = f"%{query}%"
        result = await self.db.execute(
            select(Product)
            .where(
                Product.deleted_at.is_(None),
                or_(
                    Product.title.ilike(search),
                    Product.model_number.ilike(search),
                    Product.canonical_key.ilike(search),
                ),
            )
            .limit(limit)
        )
        return list(result.scalars().all())
