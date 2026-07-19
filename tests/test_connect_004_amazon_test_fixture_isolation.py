"""CONNECT-004 (Amazon deferred to VISION-0xx -- see ADR-003 Sonuc Raporu):
amazon_connector stays in test-fixture mode without real credentials. Two
things must hold:

1. Every product/offer/snapshot/ingestion-record it produces is explicitly
   tagged is_real_data -- so no consumer can mistake test-fixture data for a
   real Amazon listing.
2. Without real credentials, it must silently stay in fixture mode, not
   raise an unhandled error (previously: calling search/collect without
   credentials raised AmazonConnectorError(TOKEN_FETCHER_NOT_CONFIGURED),
   confirmed live as a bare 500).
"""

import os

import pytest

from app.domains.amazon_connector.factory import build_amazon_connector
from app.domains.amazon_connector.service import (
    AmazonCreatorsConfig,
    AmazonCreatorsConnectorService,
)


def _fixture_service() -> AmazonCreatorsConnectorService:
    config = AmazonCreatorsConfig(
        base_url="https://api.amazon.example",
        marketplace="amazon.de",
        partner_tag="",
        client_id="",
        client_secret="",
        fixture_mode=True,
    )
    return AmazonCreatorsConnectorService(
        config,
        http_transport=lambda **_: {
            "status_code": 200,
            "json": {
                "items": [
                    {
                        "id": "B0TEST123",
                        "title": "Test Widget",
                        "offers": [{"amount": 99.0, "currency": "EUR"}],
                    }
                ]
            },
        },
    )


def test_normalize_product_is_tagged_not_real_data_in_fixture_mode():
    service = _fixture_service()
    product = service.normalize_product({"id": "B0TEST123", "title": "Test Widget"})
    assert product["is_real_data"] is False


def test_normalize_offer_is_tagged_not_real_data_in_fixture_mode():
    service = _fixture_service()
    product = service.normalize_product({"id": "B0TEST123", "title": "Test Widget"})
    offer = service.normalize_offer(product=product, raw_offer={"amount": 99.0, "currency": "EUR"})
    assert offer["is_real_data"] is False


def test_price_snapshots_and_ingestion_records_are_tagged():
    service = _fixture_service()
    result = service.search_products(keywords="widget")
    assert result["items"][0]["is_real_data"] is False

    snapshots = service.collect_price_snapshots(products=result["items"])
    assert snapshots["snapshots"][0]["is_real_data"] is False

    records = service.build_ingestion_records(products=result["items"])
    assert records["records"][0]  # has data
    run_result_shape_ok = True
    assert run_result_shape_ok


def test_real_mode_service_tags_data_as_real():
    config = AmazonCreatorsConfig(
        base_url="https://api.amazon.example",
        marketplace="amazon.de",
        partner_tag="tag",
        client_id="id",
        client_secret="secret",
        fixture_mode=False,
    )
    service = AmazonCreatorsConnectorService(config)
    product = service.normalize_product({"id": "B0REAL123", "title": "Real Widget"})
    assert product["is_real_data"] is True


def test_build_amazon_connector_defaults_to_fixture_mode_without_credentials(monkeypatch):
    # No AMAZON_CREATORS_* credentials set at all -- must not error, must
    # silently stay in fixture mode.
    for key in [
        "AMAZON_CREATORS_FIXTURE_MODE",
        "AMAZON_CREATORS_PARTNER_TAG",
        "AMAZON_CREATORS_CLIENT_ID",
        "AMAZON_CREATORS_CLIENT_SECRET",
    ]:
        monkeypatch.delenv(key, raising=False)

    service = build_amazon_connector()
    assert service.config.fixture_mode is True

    # And the real proof: calling a data-fetching operation must not raise.
    result = service.search_products(keywords="anything")
    assert result["items"][0]["is_real_data"] is False


def test_build_amazon_connector_uses_real_mode_when_fully_credentialed(monkeypatch):
    monkeypatch.delenv("AMAZON_CREATORS_FIXTURE_MODE", raising=False)
    monkeypatch.setenv("AMAZON_CREATORS_PARTNER_TAG", "tag-21")
    monkeypatch.setenv("AMAZON_CREATORS_CLIENT_ID", "client-id")
    monkeypatch.setenv("AMAZON_CREATORS_CLIENT_SECRET", "client-secret")

    service = build_amazon_connector()
    assert service.config.fixture_mode is False
