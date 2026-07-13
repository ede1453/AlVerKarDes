from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.market.connectors.registry import FeedConnectorRegistry
from app.domains.market.connectors.schemas import FeedImportResult
from app.domains.market.connectors.validators import validate_feed_item
from app.domains.market.schemas import OfferCreate, PriceSnapshotCreate
from app.domains.market.service import MarketService
from app.domains.products.service import ProductService


class FeedImportService:
    def __init__(self, db: AsyncSession, registry: FeedConnectorRegistry):
        self.market_service = MarketService(db)
        self.product_service = ProductService(db)
        self.registry = registry

    async def import_feed(self, *, connector_name: str, path: Path) -> FeedImportResult:
        connector = self.registry.get(connector_name)
        items = connector.parse(path)

        imported = 0
        errors = []

        for index, item in enumerate(items):
            validation_errors = validate_feed_item(item)
            if validation_errors:
                errors.append({"index": index, "product_title": item.product_title, "error": ",".join(validation_errors)})
                continue

            try:
                product, _identity = await self.product_service.create_from_name(item.product_title, country="DE")
                store = await self.market_service.store_repo.get_by_slug(item.store_slug)
                if not store:
                    raise ValueError(f"Unknown store_slug: {item.store_slug}")

                offer = await self.market_service.create_offer(
                    OfferCreate(product_id=product.id, store_id=store.id, url=item.product_url, store_sku=item.sku, title_on_store=item.product_title)
                )

                await self.market_service.save_price_snapshot(
                    PriceSnapshotCreate(
                        offer_id=offer.id,
                        amount=item.price,
                        currency=item.currency,
                        original_amount=item.original_price,
                        shipping_amount=item.shipping_price,
                        stock_status=item.stock_status,
                        source=connector_name,
                        observed_at=item.observed_at,
                    )
                )
                imported += 1
            except Exception as exc:
                errors.append({"index": index, "product_title": item.product_title, "error": str(exc)})

        return FeedImportResult(total_items=len(items), imported_items=imported, skipped_items=len(items) - imported, errors=errors)
