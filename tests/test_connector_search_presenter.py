from app.domains.connectors.manager import UnifiedOffer
from app.domains.connectors.search_presenter import ConnectorSearchPresenter


def test_connector_search_presenter_groups_offers():
    offers = [
        UnifiedOffer(
            source="amazon",
            title="Apple MacBook Air M5 16GB 512GB",
            canonical_key="apple::macbook-air::m5::16gb::512gb::de",
            url="https://amazon.example/a",
            price=849,
            overall_confidence=95,
            match_group_id="group::apple-mba-m5",
            match_group_score=100,
        ),
        UnifiedOffer(
            source="mediamarkt",
            title="Apple MBA M5 16/512",
            canonical_key="apple::m5::512gb::de",
            url="https://mm.example/a",
            price=879,
            overall_confidence=88,
            match_group_id="group::apple-mba-m5",
            match_group_score=88,
        ),
    ]

    payload = ConnectorSearchPresenter().present(
        query="M5",
        country="DE",
        offers=offers,
        errors=[],
    )

    assert payload["group_count"] == 1
    assert payload["offer_count"] == 2
    assert payload["groups"][0]["offer_count"] == 2
    assert payload["groups"][0]["best_offer"]["price"] == 849
    assert payload["groups"][0]["price_range"]["min"] == 849
    assert payload["groups"][0]["price_range"]["max"] == 879


def test_connector_search_presenter_separates_groups():
    offers = [
        UnifiedOffer(
            source="amazon",
            title="Apple MacBook Air M5",
            canonical_key="apple",
            price=849,
            overall_confidence=95,
            match_group_id="group-1",
        ),
        UnifiedOffer(
            source="lenovo",
            title="Lenovo ThinkPad X1",
            canonical_key="lenovo",
            price=999,
            overall_confidence=95,
            match_group_id="group-2",
        ),
    ]

    payload = ConnectorSearchPresenter().present(
        query="laptop",
        country="DE",
        offers=offers,
        errors=[],
    )

    assert payload["group_count"] == 2
