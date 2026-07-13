from app.domains.products.intelligence.cross_store_resolver import CrossStoreProductResolver


def test_cross_store_resolver_groups_by_gtin_even_when_title_differs():
    offers = [
        {
            "source": "amazon-de",
            "title": "Apple MacBook Air M5 16GB 512GB",
            "gtin": "04063879000015",
        },
        {
            "source": "mediamarkt-de",
            "title": "Apple Notebook M5 Special Edition",
            "gtin": "04063879000015",
        },
    ]

    groups = CrossStoreProductResolver().resolve(offers)

    assert len(groups) == 1
    assert groups[0].offer_count == 2


def test_cross_store_resolver_does_not_group_by_sku_only():
    offers = [
        {
            "source": "amazon-de",
            "title": "Apple MacBook Air M5 16GB 512GB",
            "sku": "SAME-SKU",
        },
        {
            "source": "other-shop",
            "title": "Dell XPS 13 16GB 512GB",
            "sku": "SAME-SKU",
        },
    ]

    groups = CrossStoreProductResolver().resolve(offers)

    assert len(groups) == 2


def test_cross_store_resolver_groups_by_mpn():
    offers = [
        {
            "source": "amazon-de",
            "title": "Apple MacBook Air M5 16GB 512GB",
            "mpn": "MBA-M5-16-512",
        },
        {
            "source": "mediamarkt-de",
            "title": "Apple Notebook Air M5",
            "mpn": "MBA M5 16 512",
        },
    ]

    groups = CrossStoreProductResolver().resolve(offers)

    assert len(groups) == 1
