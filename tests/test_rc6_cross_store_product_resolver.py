from app.domains.products.intelligence.cross_store_resolver import CrossStoreProductResolver


def test_cross_store_resolver_groups_equivalent_macbook_titles():
    offers = [
        {
            "source": "amazon-de",
            "title": "Apple MacBook Air M5 16GB 512GB Midnight",
        },
        {
            "source": "mediamarkt-de",
            "title": "Apple MBA M5 16/512 Silver",
        },
    ]

    groups = CrossStoreProductResolver().resolve(offers)

    assert len(groups) == 1
    assert groups[0].offer_count == 2
    assert groups[0].signature == "apple::macbook air::m5::16gb::512gb::de"
    assert groups[0].average_confidence >= 90


def test_cross_store_resolver_separates_different_storage():
    offers = [
        {
            "source": "amazon-de",
            "title": "Apple MacBook Air M5 16GB 512GB",
        },
        {
            "source": "mediamarkt-de",
            "title": "Apple MacBook Air M5 16GB 256GB",
        },
    ]

    groups = CrossStoreProductResolver().resolve(offers)

    assert len(groups) == 2


def test_cross_store_resolver_separates_different_brands():
    offers = [
        {
            "source": "amazon-de",
            "title": "Apple MacBook Air M5 16GB 512GB",
        },
        {
            "source": "dell-de",
            "title": "Dell XPS 13 16GB 512GB",
        },
    ]

    groups = CrossStoreProductResolver().resolve(offers)

    assert len(groups) == 2


def test_cross_store_resolver_supports_object_offers():
    class Offer:
        def __init__(self, title):
            self.title = title

    offers = [
        Offer("Apple MacBook Air M5 16GB 512GB Midnight"),
        Offer("Apple MBA M5 16/512 Silver"),
    ]

    groups = CrossStoreProductResolver().resolve(offers)

    assert len(groups) == 1
    assert groups[0].offer_count == 2
