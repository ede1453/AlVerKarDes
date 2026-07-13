from app.domains.products.merge_aware_ingestion import MergeAwareIngestionPlanner


def test_merge_aware_ingestion_assigns_duplicate_to_master():
    search_payload = {
        "groups": [
            {
                "match_group_id": "group::apple-mba-m5",
                "offers": [
                    {"source": "mock-amazon-de", "overall_confidence": 93.25},
                    {"source": "mock-mediamarkt-de", "overall_confidence": 71.25},
                ],
            }
        ]
    }

    ingestion_payload = {
        "items": [
            {
                "source": "mock-amazon-de",
                "title": "Apple MacBook Air M5 16GB 512GB",
                "canonical_key": "apple::macbook-air::m5::16gb::512gb::de",
                "product_id": "product-master",
                "offer_id": "offer-amazon",
                "status": "INGESTED",
            },
            {
                "source": "mock-mediamarkt-de",
                "title": "Apple MBA M5 16 GB 512 GB",
                "canonical_key": "apple::m5::512gb::de",
                "product_id": "product-duplicate",
                "offer_id": "offer-mediamarkt",
                "status": "INGESTED",
            },
        ]
    }

    assignments = MergeAwareIngestionPlanner().build_assignments(
        search_payload=search_payload,
        ingestion_payload=ingestion_payload,
    )

    assert len(assignments) == 1
    group = assignments[0]

    assert group.master_product_id == "product-master"
    assert group.merge_plan is not None

    remapped = [item for item in group.assignments if item.remapped]
    assert len(remapped) == 1
    assert remapped[0].original_product_id == "product-duplicate"
    assert remapped[0].assigned_product_id == "product-master"


def test_merge_aware_ingestion_applies_to_response():
    search_payload = {
        "groups": [
            {
                "match_group_id": "group::apple-mba-m5",
                "offers": [
                    {"source": "mock-amazon-de", "overall_confidence": 93.25},
                    {"source": "mock-mediamarkt-de", "overall_confidence": 71.25},
                ],
            }
        ]
    }

    ingestion_payload = {
        "items": [
            {
                "source": "mock-amazon-de",
                "title": "Apple MacBook Air M5 16GB 512GB",
                "canonical_key": "apple::macbook-air::m5::16gb::512gb::de",
                "product_id": "product-master",
                "offer_id": "offer-amazon",
                "status": "INGESTED",
            },
            {
                "source": "mock-mediamarkt-de",
                "title": "Apple MBA M5 16 GB 512 GB",
                "canonical_key": "apple::m5::512gb::de",
                "product_id": "product-duplicate",
                "offer_id": "offer-mediamarkt",
                "status": "INGESTED",
            },
        ]
    }

    result = MergeAwareIngestionPlanner().apply_to_response(
        search_payload=search_payload,
        ingestion_payload=ingestion_payload,
    )

    merge_info = result["groups"][0]["merge_aware_ingestion"]

    assert merge_info["master_product_id"] == "product-master"
    assert len(merge_info["assignments"]) == 2
    assert any(item["remapped"] for item in merge_info["assignments"])
