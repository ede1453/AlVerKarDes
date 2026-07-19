from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.internal_service_auth import require_internal_service_key
from app.domains.market.schemas import OfferCreate, PriceSnapshotCreate, StoreCreate
from app.domains.market.service import MarketService

router = APIRouter()


@router.post("/stores", status_code=status.HTTP_201_CREATED)
async def create_store(
    payload: StoreCreate,
    db: AsyncSession = Depends(get_db),
    # AUTH-004 (ADR-006): servis-arası çağrı, X-Internal-Service-Key gerektirir.
    internal_service=Depends(require_internal_service_key),
):
    store = await MarketService(db).create_store(payload)
    return {"id": store.id, "name": store.name, "slug": store.slug}


@router.post("/offers", status_code=status.HTTP_201_CREATED)
async def create_offer(
    payload: OfferCreate,
    db: AsyncSession = Depends(get_db),
    # AUTH-004 (ADR-006): servis-arası çağrı, X-Internal-Service-Key gerektirir.
    internal_service=Depends(require_internal_service_key),
):
    offer = await MarketService(db).create_offer(payload)
    return {"id": offer.id, "url": offer.url, "product_id": offer.product_id}


@router.post("/prices", status_code=status.HTTP_201_CREATED)
async def save_price(
    payload: PriceSnapshotCreate,
    db: AsyncSession = Depends(get_db),
    # AUTH-004 (ADR-006): servis-arası çağrı, X-Internal-Service-Key gerektirir.
    internal_service=Depends(require_internal_service_key),
):
    price = await MarketService(db).save_price_snapshot(payload)
    return {"id": price.id, "offer_id": price.offer_id, "amount": float(price.amount), "currency": price.currency}


@router.get("/products/{product_id}/offers")
async def get_product_offers(product_id, db: AsyncSession = Depends(get_db)):
    # CLIENT-000b (ADR-010): daha önce hiç GET endpoint'i yoktu (bu router
    # tamamen POST/yazma idi) -- frontend'in gerçek ingest edilmiş bir
    # ürünün fiyatını okuyabileceği tek yol bu. PUBLIC: /products/search
    # ile aynı sınıf, salt-okunur katalog verisi.
    pairs = await MarketService(db).get_offers_with_latest_price_for_product(product_id)
    return {
        "product_id": product_id,
        "offer_count": len(pairs),
        "offers": [
            {
                "offer_id": item["offer"].id,
                "store": item["store"].name,
                "url": item["offer"].url,
                "price": float(item["price"].amount),
                "currency": item["price"].currency,
                "stock_status": item["price"].stock_status,
                "is_real_data": item["price"].metadata_json.get("is_real_data", True),
                "observed_at": item["price"].metadata_json.get("observed_at"),
            }
            for item in pairs
        ],
    }
