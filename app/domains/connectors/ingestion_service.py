from dataclasses import dataclass, field

from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.connectors.manager import ConnectorManager, UnifiedOffer
from app.domains.market.schemas import OfferCreate, PriceSnapshotCreate, StoreCreate
from app.domains.market.service import MarketService
from app.domains.products.master_product_repository import MasterProductRepository
from app.domains.products.master_product_resolver import MasterProductResolver
from app.domains.products.service import ProductService


@dataclass
class IngestedOfferResult:
    source: str
    title: str
    canonical_key: str
    product_id: str | None
    store_id: str | None
    offer_id: str | None
    price_id: str | None
    status: str
    product_created: bool | None = None
    offer_created: bool | None = None
    error: str | None = None
    price_created: bool | None = None
    price_dedup_reason: str | None = None
    price_change: dict | None = None


@dataclass
class ConnectorIngestionResult:
    query: str
    country: str
    total_offers: int
    ingested_count: int
    skipped_count: int
    items: list[IngestedOfferResult] = field(default_factory=list)
    connector_errors: list[dict] = field(default_factory=list)


class ConnectorIngestionService:
    def __init__(self, db: AsyncSession, manager: ConnectorManager):
        self.db = db
        self.manager = manager
        self.product_service = ProductService(db)
        self.market_service = MarketService(db)
        self.master_product_repo = MasterProductRepository(db)
        self.master_product_resolver = MasterProductResolver()

    async def _resolve_existing_master_product_id(self, *, offer, grouped_offers: list[dict] | None = None):
        if not hasattr(self.db, "execute"):
            return None

        urls = []

        if grouped_offers:
            urls = [item.get("url") for item in grouped_offers if item.get("url")]

        if not urls and getattr(offer, "url", None):
            urls = [offer.url]

        if not urls:
            return None

        resolution = await self.master_product_resolver.resolve_from_group(
            repo=self.master_product_repo,
            group={"offers": [{"url": url} for url in urls]},
        )

        return resolution.master_product_id

    async def search_and_ingest(self, query: str, country: str = "DE") -> ConnectorIngestionResult:
        search_result = await self.manager.search_all(query=query, country=country)

        items: list[IngestedOfferResult] = []
        ingested_count = 0

        for offer in search_result.offers:
            item = await self._ingest_offer(offer=offer, country=country, grouped_offers=search_result.offers)
            items.append(item)
            if item.status == "INGESTED":
                ingested_count += 1

        return ConnectorIngestionResult(
            query=query,
            country=country,
            total_offers=len(search_result.offers),
            ingested_count=ingested_count,
            skipped_count=len(search_result.offers) - ingested_count,
            items=items,
            connector_errors=search_result.errors,
        )

    async def _ingest_offer(
        self,
        offer: UnifiedOffer,
        country: str,
        grouped_offers: list[UnifiedOffer] | None = None,
    ) -> IngestedOfferResult:
        if offer.price is None:
            return IngestedOfferResult(
                source=offer.source,
                title=offer.title,
                canonical_key=offer.canonical_key,
                product_id=None,
                store_id=None,
                offer_id=None,
                price_id=None,
                status="SKIPPED",
                error="missing_price",
            )

        if not offer.url:
            return IngestedOfferResult(
                source=offer.source,
                title=offer.title,
                canonical_key=offer.canonical_key,
                product_id=None,
                store_id=None,
                offer_id=None,
                price_id=None,
                status="SKIPPED",
                error="missing_url",
            )

        try:
            existing_master_product_id = await self._resolve_existing_master_product_id(
                offer=offer,
                grouped_offers=[
                    {"url": item.url, "source": item.source}
                    for item in grouped_offers or []
                ],
            )

            if existing_master_product_id:
                product_id = existing_master_product_id
                product_created = False
            else:
                product, _identity, product_created = await self.product_service.get_or_create_product(
                    product_name=offer.title,
                    country=country,
                )
                product_id = product.id

            store = await self.market_service.create_store(
                StoreCreate(
                    name=offer.source,
                    slug=self._slugify(offer.source),
                    website=self._store_website_from_url(offer.url),
                    country=country,
                    affiliate_enabled=False,
                    trust_score=max(min(offer.overall_confidence, 100), 0),
                )
            )

            db_offer, offer_created = await self.market_service.get_or_create_offer(
                OfferCreate(
                    product_id=product_id,
                    store_id=store.id,
                    url=offer.url,
                    store_sku=offer.sku,
                    title_on_store=offer.title,
                )
            )

            price = await self.market_service.save_price_snapshot(
                PriceSnapshotCreate(
                    offer_id=db_offer.id,
                    amount=offer.price,
                    currency=offer.currency,
                    stock_status=offer.availability,
                    source=f"connector:{offer.source}",
                )
            )

            return IngestedOfferResult(
                source=offer.source,
                title=offer.title,
                canonical_key=offer.canonical_key,
                product_id=str(product_id),
                store_id=str(store.id),
                offer_id=str(db_offer.id),
                price_id=str(price.id),
                status="INGESTED",
                product_created=product_created,
                offer_created=offer_created,
                price_created=getattr(price, "_price_created", True),
                price_dedup_reason=getattr(price, "_price_dedup_reason", None),
                price_change=self._serialize_price_change(price),
            )
        except Exception as exc:
            await self.db.rollback()
            return IngestedOfferResult(
                source=offer.source,
                title=offer.title,
                canonical_key=offer.canonical_key,
                product_id=None,
                store_id=None,
                offer_id=None,
                price_id=None,
                status="ERROR",
                error=str(exc),
            )

    def _serialize_price_change(self, price):
        change = getattr(price, "_price_change", None)
        if not change:
            return None

        return {
            "changed": change.changed,
            "direction": change.direction,
            "previous_amount": str(change.previous_amount) if change.previous_amount is not None else None,
            "current_amount": str(change.current_amount),
            "change_amount": str(change.change_amount),
            "change_percent": str(change.change_percent),
        }

    def _slugify(self, value: str) -> str:
        cleaned = value.lower().strip()
        cleaned = cleaned.replace("https://", "").replace("http://", "")
        for char in [" ", "_", ".", "/"]:
            cleaned = cleaned.replace(char, "-")
        while "--" in cleaned:
            cleaned = cleaned.replace("--", "-")
        return cleaned.strip("-")[:220]

    def _store_website_from_url(self, url: str) -> str | None:
        if "://" not in url:
            return None
        parts = url.split("/")
        if len(parts) >= 3:
            return f"{parts[0]}//{parts[2]}"
        return None