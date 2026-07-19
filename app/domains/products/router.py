from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.domains.deals.offer_deal_summary_service import OfferDealSummaryService
from app.domains.market.service import MarketService
from app.domains.products.schemas import BrandCreate, CategoryCreate, ProductCreate
from app.domains.products.service import ProductService
from app.domains.identity.dependencies import get_current_user, require_role
from app.domains.identity.models import UserRole

router = APIRouter()


@router.post("/brands", status_code=status.HTTP_201_CREATED)
async def create_brand(
    payload: BrandCreate,
    db: AsyncSession = Depends(get_db),
    # AUTH-006 Parça 3 (ADR-005): OPERATOR+ gerektirir.
    current_user=Depends(require_role(UserRole.OPERATOR)),
):
    brand = await ProductService(db).create_brand(payload)
    return {"id": brand.id, "name": brand.name, "slug": brand.slug}


@router.post("/categories", status_code=status.HTTP_201_CREATED)
async def create_category(
    payload: CategoryCreate,
    db: AsyncSession = Depends(get_db),
    # AUTH-006 Parça 3 (ADR-005): OPERATOR+ gerektirir.
    current_user=Depends(require_role(UserRole.OPERATOR)),
):
    category = await ProductService(db).create_category(payload)
    return {"id": category.id, "name": category.name, "slug": category.slug}


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_product(
    payload: ProductCreate,
    db: AsyncSession = Depends(get_db),
    # AUTH-006 Parça 3 (ADR-005): OPERATOR+ gerektirir.
    current_user=Depends(require_role(UserRole.OPERATOR)),
):
    product = await ProductService(db).create_product(payload)
    return {"id": product.id, "title": product.title, "canonical_key": product.canonical_key}


@router.post("/from-name", status_code=status.HTTP_201_CREATED)
async def create_product_from_name(
    product_name: str,
    country: str = "DE",
    db: AsyncSession = Depends(get_db),
    # AUTH-006 Parça 3 (ADR-005): OPERATOR+ gerektirir.
    current_user=Depends(require_role(UserRole.OPERATOR)),
):
    product, identity, _created = await ProductService(db).create_from_name(product_name, country)
    return {"id": product.id, "title": product.title, "canonical_key": product.canonical_key, "identity": identity.model_dump()}


@router.get("/search")
async def search_products(q: str = Query(min_length=2), limit: int = Query(default=20, ge=1, le=50), db: AsyncSession = Depends(get_db)):
    products = await ProductService(db).search_products(q, limit)
    return {"items": [{"id": item.id, "title": item.title, "canonical_key": item.canonical_key} for item in products]}


@router.get("/{product_id}/detail")
async def get_product_detail(product_id: UUID, db: AsyncSession = Depends(get_db)):
    # CLIENT-002b: CLIENT-002a'nin (ADR-011) planladigi toplayici PUBLIC
    # endpoint -- Next.js SSR urun detay sayfasinin tek cagrida ihtiyac
    # duydugu her seyi dondurur. Var olan 3 gercek veri kaynagini birlestirir,
    # hicbirini yeniden uygulamaz: MarketService.get_offers_with_latest_price_for_product
    # (GET /market/products/{id}/offers ile ayni), yeni paylasilan
    # MarketService.get_price_history_summary_for_product (shopping_pipeline
    # ile ayni gercek market.Price ozeti), OfferDealSummaryService (GET
    # /deals/offers/{offer_id}/summary ile ayni, gercek DB'den okuyor).
    # POST /deal-intelligence/evaluate BILEREK kullanilmadi -- o durumsuz bir
    # hesaplayici, caller'in fiyat listesini elle vermesini gerektiriyor;
    # burada zaten elimizde olan gercek veriyi tekrar paketlemek yerine
    # zaten-gercek-veri-okuyan OfferDealSummaryService tercih edildi.
    product = await ProductService(db).get_by_id(product_id)
    if product is None:
        raise HTTPException(status_code=404, detail="product_not_found")

    market_service = MarketService(db)
    offer_pairs = await market_service.get_offers_with_latest_price_for_product(product_id)
    price_history = await market_service.get_price_history_summary_for_product(product_id)

    deal_signal = None
    if offer_pairs:
        cheapest = min(offer_pairs, key=lambda item: item["price"].amount)
        try:
            deal_signal = await OfferDealSummaryService(db).summarize_offer(offer_id=cheapest["offer"].id)
        except ValueError:
            deal_signal = None

    return {
        "product": {
            "id": product.id,
            "title": product.title,
            "canonical_key": product.canonical_key,
        },
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
            for item in offer_pairs
        ],
        "price_history": price_history,
        "deal_signal": deal_signal,
    }
