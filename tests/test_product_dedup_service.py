import pytest

from app.domains.products.schemas import ProductCreate


class DummyProduct:
    def __init__(self, id, canonical_key):
        self.id = id
        self.canonical_key = canonical_key


class FakeProductRepository:
    def __init__(self):
        self.products = {}
        self.created_count = 0

    async def get_by_canonical_key(self, key: str):
        return self.products.get(key)

    async def create(self, payload: ProductCreate):
        self.created_count += 1
        product = DummyProduct(
            id=f"product-{self.created_count}",
            canonical_key=payload.canonical_key,
        )
        self.products[payload.canonical_key] = product
        return product


@pytest.mark.asyncio
async def test_get_or_create_product_reuses_canonical_key():
    from app.domains.products.service import ProductService

    service = ProductService(db=None)
    fake_repo = FakeProductRepository()
    service.product_repo = fake_repo

    first, first_identity, first_created = await service.get_or_create_product(
        "Apple MacBook Air M5 16GB 512GB"
    )
    second, second_identity, second_created = await service.get_or_create_product(
        "Apple MacBook Air M5 16 GB 512 GB"
    )

    assert first_identity.canonical_key == second_identity.canonical_key
    assert first.id == second.id
    assert first_created is True
    assert second_created is False
    assert fake_repo.created_count == 1
