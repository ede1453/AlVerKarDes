import pytest

from app.domains.connectors.manager import ConnectorManager
from app.domains.connectors.manual_connector import ManualConnector
from app.domains.connectors.sdk import ConnectorProductResult


@pytest.mark.asyncio
async def test_connector_manager_groups_aliases_with_product_match_engine():
    manager = ConnectorManager([
        ManualConnector([
            ConnectorProductResult(
                source="amazon",
                title="Apple MacBook Air M5 16GB 512GB",
                url="https://amazon.example/macbook-air-m5-16-512",
                price=849,
                confidence=95,
            ),
            ConnectorProductResult(
                source="mediamarkt",
                title="Apple MBA M5 16/512",
                url="https://mediamarkt.example/apple-mba-m5-16-512",
                price=879,
                confidence=90,
            ),
            ConnectorProductResult(
                source="saturn",
                title="MacBook Air M5 (16 GB RAM, 512 GB SSD)",
                url="https://saturn.example/macbook-air-m5-16gb-512gb",
                price=869,
                confidence=90,
            ),
        ])
    ])

    result = await manager.search_all("M5")

    assert len(result.offers) == 3

    group_ids = {offer.match_group_id for offer in result.offers}
    assert len(group_ids) == 1

    for offer in result.offers:
        assert offer.match_group_score is not None
        assert offer.match_group_score >= 86


@pytest.mark.asyncio
async def test_connector_manager_does_not_group_different_products():
    manager = ConnectorManager([
        ManualConnector([
            ConnectorProductResult(
                source="amazon",
                title="Apple MacBook Air M5 16GB 512GB",
                url="https://amazon.example/macbook",
                price=849,
                confidence=95,
            ),
            ConnectorProductResult(
                source="lenovo",
                title="Lenovo ThinkPad X1 16GB 512GB",
                url="https://lenovo.example/thinkpad",
                price=999,
                confidence=95,
            ),
        ])
    ])

    result = await manager.search_all("")

    group_ids = {offer.match_group_id for offer in result.offers}
    assert len(group_ids) == 2
