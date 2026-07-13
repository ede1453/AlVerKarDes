from decimal import Decimal
from pathlib import Path

import pytest

from app.domains.connectors.adapters.mediamarkt_de import MediaMarktDEConnector
from app.domains.connectors.parsers.mediamarkt_parser import MediaMarktProductParser


def test_mediamarkt_parser_parses_fixture():
    raw = Path("tests/fixtures/mediamarkt_search_m5.json").read_text(encoding="utf-8")

    offers = MediaMarktProductParser().parse_json_items(raw)

    assert len(offers) == 2
    assert offers[0].source == "mediamarkt-de"
    assert offers[0].title == "Apple MacBook Air M5 16 GB 512 GB"
    assert offers[0].price == Decimal("879.00")
    assert offers[0].currency == "EUR"
    assert offers[0].availability == "in_stock"


@pytest.mark.asyncio
async def test_mediamarkt_connector_searches_fixture():
    raw = Path("tests/fixtures/mediamarkt_search_m5.json").read_text(encoding="utf-8")

    connector = MediaMarktDEConnector(fixture_json=raw)

    offers = await connector.search("M5")

    assert len(offers) == 2
    assert all("M5" in offer.title for offer in offers)


@pytest.mark.asyncio
async def test_mediamarkt_connector_returns_empty_without_fixture():
    connector = MediaMarktDEConnector()

    offers = await connector.search("M5")

    assert offers == []
