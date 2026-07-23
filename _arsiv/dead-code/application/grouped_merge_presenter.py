from app.domains.products.merge_service import ProductMergeCandidate, ProductMergeService


class GroupedMergePresenter:
    def __init__(self):
        self.merge_service = ProductMergeService()

    def attach_merge_plans(self, *, search_payload: dict, ingestion_payload: dict) -> dict:
        groups = search_payload.get("groups", [])
        ingested_items = ingestion_payload.get("items", [])

        for group in groups:
            group["merge_plan"] = self._build_group_merge_plan(
                group=group,
                ingested_items=ingested_items,
            )

        return search_payload

    def _build_group_merge_plan(self, *, group: dict, ingested_items: list[dict]) -> dict | None:
        group_sources = {
            offer.get("source")
            for offer in group.get("offers", [])
            if offer.get("source")
        }

        candidates = []

        for item in ingested_items:
            if item.get("status") != "INGESTED":
                continue

            if item.get("source") not in group_sources:
                continue

            candidates.append(
                ProductMergeCandidate(
                    product_id=item.get("product_id"),
                    canonical_key=item.get("canonical_key"),
                    title=item.get("title"),
                    confidence=self._source_confidence(group, item.get("source")),
                    source=item.get("source"),
                    metadata={
                        "offer_id": item.get("offer_id"),
                        "price_id": item.get("price_id"),
                    },
                )
            )

        plan = self.merge_service.build_merge_plan(candidates)
        if not plan:
            return None

        return {
            "master_product_id": plan.master_product_id,
            "master_canonical_key": plan.master_canonical_key,
            "duplicate_product_ids": plan.duplicate_product_ids,
            "canonical_keys": plan.canonical_keys,
            "confidence": plan.confidence,
            "reason": plan.reason,
            "candidate_count": plan.candidate_count,
        }

    def _source_confidence(self, group: dict, source: str | None) -> float:
        if not source:
            return 0.0

        for offer in group.get("offers", []):
            if offer.get("source") == source:
                return float(offer.get("overall_confidence") or 0)

        return 0.0
