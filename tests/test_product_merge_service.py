from app.domains.products.merge_service import ProductMergeCandidate, ProductMergeService


def test_product_merge_service_selects_most_complete_master():
    service = ProductMergeService()

    plan = service.build_merge_plan([
        ProductMergeCandidate(
            product_id="product-a",
            canonical_key="apple::m5::512gb::de",
            title="Apple MBA M5 16 GB 512 GB",
            confidence=71.25,
            source="mock-mediamarkt-de",
        ),
        ProductMergeCandidate(
            product_id="product-b",
            canonical_key="apple::macbook-air::m5::16gb::512gb::de",
            title="Apple MacBook Air M5 16GB 512GB",
            confidence=93.25,
            source="mock-amazon-de",
        ),
    ])

    assert plan is not None
    assert plan.master_product_id == "product-b"
    assert plan.master_canonical_key == "apple::macbook-air::m5::16gb::512gb::de"
    assert plan.duplicate_product_ids == ["product-a"]
    assert plan.confidence >= 80


def test_product_merge_service_returns_none_for_single_candidate():
    service = ProductMergeService()

    plan = service.build_merge_plan([
        ProductMergeCandidate(
            product_id="product-a",
            canonical_key="apple::macbook-air::m5::16gb::512gb::de",
            title="Apple MacBook Air M5 16GB 512GB",
            confidence=93.25,
        )
    ])

    assert plan is None


def test_product_merge_service_handles_same_product_id():
    service = ProductMergeService()

    plan = service.build_merge_plan([
        ProductMergeCandidate(
            product_id="product-a",
            canonical_key="apple::macbook-air::m5::16gb::512gb::de",
            title="Apple MacBook Air M5",
            confidence=90,
        ),
        ProductMergeCandidate(
            product_id="product-a",
            canonical_key="apple::macbook-air::m5::16gb::512gb::de",
            title="Apple MacBook Air M5",
            confidence=90,
        ),
    ])

    assert plan is None
