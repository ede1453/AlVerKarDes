from app.domains.products.master_product_repository import MasterProductRepository
from app.domains.products.master_product_resolver import MasterProductResolver


class ConnectorMasterResolutionService:
    def __init__(self, db):
        self.repo = MasterProductRepository(db)
        self.resolver = MasterProductResolver()

    async def resolve_master_for_offer(self, *, offer, grouped_offers: list[dict]) -> dict:
        group = {
            "offers": grouped_offers or [
                {
                    "source": getattr(offer, "source", None),
                    "url": getattr(offer, "url", None),
                }
            ]
        }

        resolution = await self.resolver.resolve_from_group(
            repo=self.repo,
            group=group,
        )

        return {
            "master_product_id": resolution.master_product_id,
            "source": resolution.source,
            "confidence": resolution.confidence,
            "reason": resolution.reason,
        }
