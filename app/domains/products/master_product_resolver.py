from dataclasses import dataclass


@dataclass
class MasterProductResolution:
    master_product_id: str | None
    source: str
    confidence: float
    reason: str


class MasterProductResolver:
    async def resolve_from_group(self, *, repo, group: dict) -> MasterProductResolution:
        urls = [offer.get("url") for offer in group.get("offers", []) if offer.get("url")]

        if not urls:
            return MasterProductResolution(None, "none", 0, "no_offer_urls")

        active_products = await repo.get_active_product_ids_by_offer_urls(urls)

        if not active_products:
            return MasterProductResolution(None, "none", 0, "no_existing_active_product_for_group")

        ranked = sorted(
            active_products,
            key=lambda item: (item.get("offer_count", 0), item.get("canonical_quality", 0)),
            reverse=True,
        )

        return MasterProductResolution(
            master_product_id=str(ranked[0]["product_id"]),
            source="existing_group_offer",
            confidence=95,
            reason="active_offer_in_same_match_group",
        )
