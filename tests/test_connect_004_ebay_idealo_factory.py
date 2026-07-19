"""CONNECT-004 (eBay/Idealo, redefined scope -- see ADR-007 CONNECT-004
Sonuc Raporu): env-driven factory for marketplace_connectors. Three things
must hold:

1. Without real credentials, build_ebay_connector()/build_idealo_connector()
   default to fixture mode and read the real fixture files (previously:
   marketplace_connectors_router.py hardcoded a lambda that always returned
   an empty result, ignoring both credentials and fixtures/ entirely).
2. With real credentials configured via env vars, fixture_mode flips to
   False (previously: env vars were never read at all).
3. Every ebay/idealo output dict is tagged is_real_data.
"""

import os

from app.domains.marketplace_connectors.factory import (
    build_ebay_connector,
    build_idealo_connector,
    idealo_fixture_feed_content,
)

_EBAY_ENV_KEYS = [
    "EBAY_FIXTURE_MODE",
    "EBAY_CLIENT_ID",
    "EBAY_CLIENT_SECRET",
]
_IDEALO_ENV_KEYS = [
    "IDEALO_FIXTURE_MODE",
    "IDEALO_PARTNER_ID",
    "IDEALO_API_KEY",
]


def test_build_ebay_connector_defaults_to_fixture_mode_without_credentials(monkeypatch):
    for key in _EBAY_ENV_KEYS:
        monkeypatch.delenv(key, raising=False)

    service = build_ebay_connector()
    assert service.config.fixture_mode is True

    # Real proof: search must not raise, and must return the real fixture
    # file's content, not a hardcoded empty result.
    result = service.search_items(query="anything")
    assert result["item_count"] == 1
    assert result["items"][0]["is_real_data"] is False
    assert result["items"][0]["title"] == "Example Laptop"


def test_build_ebay_connector_uses_real_mode_when_credentialed(monkeypatch):
    monkeypatch.delenv("EBAY_FIXTURE_MODE", raising=False)
    monkeypatch.setenv("EBAY_CLIENT_ID", "real-client-id")
    monkeypatch.setenv("EBAY_CLIENT_SECRET", "real-client-secret")

    service = build_ebay_connector()
    assert service.config.fixture_mode is False


def test_build_ebay_connector_treats_change_me_placeholder_as_missing(monkeypatch):
    monkeypatch.delenv("EBAY_FIXTURE_MODE", raising=False)
    monkeypatch.setenv("EBAY_CLIENT_ID", "CHANGE_ME")
    monkeypatch.setenv("EBAY_CLIENT_SECRET", "CHANGE_ME")

    service = build_ebay_connector()
    assert service.config.fixture_mode is True


def test_build_idealo_connector_defaults_to_fixture_mode_without_credentials(monkeypatch):
    for key in _IDEALO_ENV_KEYS:
        monkeypatch.delenv(key, raising=False)

    service = build_idealo_connector()
    assert service.config.fixture_mode is True

    content = idealo_fixture_feed_content()
    result = service.run_feed_collection(content=content, format="csv")
    assert result["offer_count"] == 1
    assert result["offers"][0]["is_real_data"] is False
    assert result["is_real_data"] is False


def test_build_idealo_connector_uses_real_mode_when_credentialed(monkeypatch):
    monkeypatch.delenv("IDEALO_FIXTURE_MODE", raising=False)
    monkeypatch.setenv("IDEALO_PARTNER_ID", "real-partner")
    monkeypatch.setenv("IDEALO_API_KEY", "real-key")

    service = build_idealo_connector()
    assert service.config.fixture_mode is False
