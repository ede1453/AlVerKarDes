from app.domains.application.grouped_merge_presenter import GroupedMergePresenter


def test_grouped_merge_presenter_attaches_merge_plan():
    search_payload = {
        "groups": [
            {
                "match_group_id": "group::apple-mba-m5",
                "offers": [
                    {
                        "source": "mock-amazon-de",
                        "overall_confidence": 93.25,
                    },
                    {
                        "source": "mock-mediamarkt-de",
                        "overall_confidence": 71.25,
                    },
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
                "product_id": "product-amazon",
                "offer_id": "offer-amazon",
                "price_id": "price-amazon",
                "status": "INGESTED",
            },
            {
                "source": "mock-mediamarkt-de",
                "title": "Apple MBA M5 16 GB 512 GB",
                "canonical_key": "apple::m5::512gb::de",
                "product_id": "product-mediamarkt",
                "offer_id": "offer-mediamarkt",
                "price_id": "price-mediamarkt",
                "status": "INGESTED",
            },
        ]
    }

    result = GroupedMergePresenter().attach_merge_plans(
        search_payload=search_payload,
        ingestion_payload=ingestion_payload,
    )

    merge_plan = result["groups"][0]["merge_plan"]

    assert merge_plan is not None
    assert merge_plan["master_product_id"] == "product-amazon"
    assert merge_plan["duplicate_product_ids"] == ["product-mediamarkt"]
    assert merge_plan["candidate_count"] == 2


def test_grouped_merge_presenter_no_plan_for_single_product():
    search_payload = {
        "groups": [
            {
                "match_group_id": "group::apple-mba-m5",
                "offers": [
                    {
                        "source": "mock-amazon-de",
                        "overall_confidence": 93.25,
                    },
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
                "product_id": "product-amazon",
                "status": "INGESTED",
            },
        ]
    }

    result = GroupedMergePresenter().attach_merge_plans(
        search_payload=search_payload,
        ingestion_payload=ingestion_payload,
    )

    assert result["groups"][0]["merge_plan"] is None
