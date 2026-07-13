from decimal import Decimal
from pathlib import Path

import pytest

from app.domains.connectors.adapters.amazon_de import AmazonDEConnector
from app.domains.connectors.parsers.amazon_parser import AmazonProductParser


def test_amazon_parser_parses_fixture():
    raw = Path("tests/fixtures/amazon_search_m5.json").read_text(encoding="utf-8")

    offers = AmazonProductParser().parse_json_items(raw)

    assert len(offers) == 2
    assert offers[0].source == "amazon-de"
    assert offers[0].title == "Apple MacBook Air M5 16GB 512GB"
    assert offers[0].price == Decimal("849.00")
    assert offers[0].currency == "EUR"
    assert offers[0].sku == "B0M5AIR16512"


@pytest.mark.asyncio
async def test_amazon_connector_searches_fixture():
    raw = Path("tests/fixtures/amazon_search_m5.json").read_text(encoding="utf-8")

    connector = AmazonDEConnector(fixture_json=raw)

    offers = await connector.search("M5")

    assert len(offers) == 2
    assert all("M5" in offer.title for offer in offers)


@pytest.mark.asyncio
async def test_amazon_connector_returns_empty_without_fixture():
    connector = AmazonDEConnector()

    offers = await connector.search("M5")

    assert offers == []
