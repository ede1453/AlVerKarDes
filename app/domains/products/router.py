from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.domains.products.schemas import BrandCreate, CategoryCreate, ProductCreate
from app.domains.products.service import ProductService

router = APIRouter()


@router.post("/brands", status_code=status.HTTP_201_CREATED)
async def create_brand(payload: BrandCreate, db: AsyncSession = Depends(get_db)):
    brand = await ProductService(db).create_brand(payload)
    return {"id": brand.id, "name": brand.name, "slug": brand.slug}


@router.post("/categories", status_code=status.HTTP_201_CREATED)
async def create_category(payload: CategoryCreate, db: AsyncSession = Depends(get_db)):
    category = await ProductService(db).create_category(payload)
    return {"id": category.id, "name": category.name, "slug": category.slug}


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_product(payload: ProductCreate, db: AsyncSession = Depends(get_db)):
    product = await ProductService(db).create_product(payload)
    return {"id": product.id, "title": product.title, "canonical_key": product.canonical_key}


@router.post("/from-name", status_code=status.HTTP_201_CREATED)
async def create_product_from_name(product_name: str, country: str = "DE", db: AsyncSession = Depends(get_db)):
    product, identity = await ProductService(db).create_from_name(product_name, country)
    return {"id": product.id, "title": product.title, "canonical_key": product.canonical_key, "identity": identity.model_dump()}


@router.get("/search")
async def search_products(q: str = Query(min_length=2), limit: int = Query(default=20, ge=1, le=50), db: AsyncSession = Depends(get_db)):
    products = await ProductService(db).search_products(q, limit)
    return {"items": [{"id": item.id, "title": item.title, "canonical_key": item.canonical_key} for item in products]}
