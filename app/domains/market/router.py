from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.domains.market.schemas import OfferCreate, PriceSnapshotCreate, StoreCreate
from app.domains.market.service import MarketService

router = APIRouter()


@router.post("/stores", status_code=status.HTTP_201_CREATED)
async def create_store(payload: StoreCreate, db: AsyncSession = Depends(get_db)):
    store = await MarketService(db).create_store(payload)
    return {"id": store.id, "name": store.name, "slug": store.slug}


@router.post("/offers", status_code=status.HTTP_201_CREATED)
async def create_offer(payload: OfferCreate, db: AsyncSession = Depends(get_db)):
    offer = await MarketService(db).create_offer(payload)
    return {"id": offer.id, "url": offer.url, "product_id": offer.product_id}


@router.post("/prices", status_code=status.HTTP_201_CREATED)
async def save_price(payload: PriceSnapshotCreate, db: AsyncSession = Depends(get_db)):
    price = await MarketService(db).save_price_snapshot(payload)
    return {"id": price.id, "offer_id": price.offer_id, "amount": float(price.amount), "currency": price.currency}
