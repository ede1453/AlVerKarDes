from app.domains.product_canonicalization.canonical_engine import ProductCanonicalizationEngine


def test_canonicalization_engine_groups_same_product_variants():
    result = ProductCanonicalizationEngine().canonicalize(
        query="MacBook Air",
        offers=[
            {"id": "1", "product_name": "Apple MacBook Air M3 13 inch 512GB", "marketplace": "amazon"},
            {"id": "2", "product_name": "Apple MacBook Air M3 13 inch 512GB", "marketplace": "saturn"},
            {"id": "3", "product_name": "Apple iPhone 16 128GB", "marketplace": "otto"},
        ],
    )

    assert result.canonical_count == 2
    assert result.products[0].brand == "apple"
    assert result.products[0].confidence >= 90
    assert len(result.products[0].source_offer_ids) == 2
