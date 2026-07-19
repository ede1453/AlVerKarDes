from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.products.normalization.schemas import ProductNormalizationInput
from app.domains.products.normalization.service import ProductNormalizationService
from app.domains.products.repository import BrandRepository, CategoryRepository, ProductRepository
from app.domains.products.schemas import BrandCreate, CategoryCreate, ProductCreate


class ProductService:
    def __init__(self, db: AsyncSession):
        self.brand_repo = BrandRepository(db)
        self.category_repo = CategoryRepository(db)
        self.product_repo = ProductRepository(db)
        self.normalizer = ProductNormalizationService()

    async def create_brand(self, payload: BrandCreate):
        return await self.brand_repo.create(payload)

    async def create_category(self, payload: CategoryCreate):
        return await self.category_repo.create(payload)

    async def create_product(self, payload: ProductCreate):
        return await self.product_repo.create(payload)

    async def search_products(self, query: str, limit: int = 20):
        return await self.product_repo.search(query, limit)

    async def get_by_id(self, product_id):
        return await self.product_repo.get_by_id(product_id)

    async def create_from_name(self, product_name: str, country: str = "DE"):
        return await self.get_or_create_product(product_name=product_name, country=country)

    async def get_or_create_product(self, product_name: str, country: str = "DE"):
        identity = self.normalizer.normalize(
            ProductNormalizationInput(product_name=product_name, country=country)
        )

        if identity.canonical_key:
            existing = await self.product_repo.get_by_canonical_key(identity.canonical_key)
            if existing:
                return existing, identity, False

        product = await self.product_repo.create(
            ProductCreate(
                title=product_name,
                canonical_key=identity.canonical_key,
                model_number=identity.model,
                metadata={
                    "normalized_identity": identity.model_dump(),
                    "normalization_confidence": identity.confidence,
                    "created_by": "get_or_create_product",
                },
            )
        )
        return product, identity, True
