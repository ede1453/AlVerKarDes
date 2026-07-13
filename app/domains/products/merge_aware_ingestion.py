from dataclasses import dataclass

from app.domains.products.merge_service import ProductMergeCandidate, ProductMergeService


@dataclass
class MergeAwareOfferAssignment:
    source: str
    original_product_id: str | None
    assigned_product_id: str | None
    offer_id: str | None
    canonical_key: str | None
    title: str | None
    is_master: bool
    remapped: bool


@dataclass
class MergeAwareGroupAssignment:
    match_group_id: str
    master_product_id: str | None
    master_canonical_key: str | None
    assignments: list[MergeAwareOfferAssignment]
    merge_plan: dict | None


class MergeAwareIngestionPlanner:
    def __init__(self):
        self.merge_service = ProductMergeService()

    def build_assignments(self, *, search_payload: dict, ingestion_payload: dict) -> list[MergeAwareGroupAssignment]:
        groups = search_payload.get("groups", [])
        items = ingestion_payload.get("items", [])

        assignments: list[MergeAwareGroupAssignment] = []

        for group in groups:
            assignments.append(
                self._build_group_assignment(group=group, ingested_items=items)
            )

        return assignments

    def _build_group_assignment(self, *, group: dict, ingested_items: list[dict]) -> MergeAwareGroupAssignment:
        group_id = group.get("match_group_id")
        group_sources = {
            offer.get("source")
            for offer in group.get("offers", [])
            if offer.get("source")
        }

        candidates = []
        group_items = []

        for item in ingested_items:
            if item.get("status") != "INGESTED":
                continue

            if item.get("source") not in group_sources:
                continue

            group_items.append(item)
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

        master_product_id = None
        master_canonical_key = None
        merge_plan_dict = None

        if plan:
            master_product_id = plan.master_product_id
            master_canonical_key = plan.master_canonical_key
            merge_plan_dict = {
                "master_product_id": plan.master_product_id,
                "master_canonical_key": plan.master_canonical_key,
                "duplicate_product_ids": plan.duplicate_product_ids,
                "canonical_keys": plan.canonical_keys,
                "confidence": plan.confidence,
                "reason": plan.reason,
                "candidate_count": plan.candidate_count,
            }
        elif group_items:
            master_product_id = group_items[0].get("product_id")
            master_canonical_key = group_items[0].get("canonical_key")

        assignments = []

        for item in group_items:
            original_product_id = item.get("product_id")
            assigned_product_id = master_product_id or original_product_id

            assignments.append(
                MergeAwareOfferAssignment(
                    source=item.get("source"),
                    original_product_id=original_product_id,
                    assigned_product_id=assigned_product_id,
                    offer_id=item.get("offer_id"),
                    canonical_key=item.get("canonical_key"),
                    title=item.get("title"),
                    is_master=original_product_id == master_product_id,
                    remapped=bool(master_product_id and original_product_id != master_product_id),
                )
            )

        return MergeAwareGroupAssignment(
            match_group_id=group_id,
            master_product_id=master_product_id,
            master_canonical_key=master_canonical_key,
            assignments=assignments,
            merge_plan=merge_plan_dict,
        )

    def apply_to_response(self, *, search_payload: dict, ingestion_payload: dict) -> dict:
        group_assignments = self.build_assignments(
            search_payload=search_payload,
            ingestion_payload=ingestion_payload,
        )

        by_group_id = {
            item.match_group_id: item
            for item in group_assignments
        }

        for group in search_payload.get("groups", []):
            assignment = by_group_id.get(group.get("match_group_id"))

            if not assignment:
                group["merge_aware_ingestion"] = None
                continue

            group["merge_aware_ingestion"] = {
                "master_product_id": assignment.master_product_id,
                "master_canonical_key": assignment.master_canonical_key,
                "merge_plan": assignment.merge_plan,
                "assignments": [
                    {
                        "source": item.source,
                        "original_product_id": item.original_product_id,
                        "assigned_product_id": item.assigned_product_id,
                        "offer_id": item.offer_id,
                        "canonical_key": item.canonical_key,
                        "title": item.title,
                        "is_master": item.is_master,
                        "remapped": item.remapped,
                    }
                    for item in assignment.assignments
                ],
            }

        return search_payload

    def _source_confidence(self, group: dict, source: str | None) -> float:
        if not source:
            return 0.0

        for offer in group.get("offers", []):
            if offer.get("source") == source:
                return float(offer.get("overall_confidence") or 0)

        return 0.0
