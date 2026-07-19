from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any
from urllib.parse import urlencode

from app.domains.marketplace_connectors.service import (
    BestBuyConfig,
    BestBuyConnectorService,
    EbayBrowseConfig,
    EbayBrowseConnectorService,
    IdealoPartnerConfig,
    IdealoPartnerConnectorService,
)


def _fixture_transport(fixture_path: Path):
    def transport(**_: Any) -> dict[str, Any]:
        return {
            "status_code": 200,
            "json": json.loads(fixture_path.read_text(encoding="utf-8")),
        }

    return transport


def _ebay_http_transport(*, method: str, url: str, headers: dict[str, str]) -> dict[str, Any]:
    request = urllib.request.Request(url=url, headers=headers, method=method)
    try:
        with urllib.request.urlopen(request, timeout=15) as response:
            return {
                "status_code": response.status,
                "json": json.loads(response.read().decode("utf-8")),
            }
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8")
        try:
            payload = json.loads(raw)
        except ValueError:
            payload = {"message": raw}
        return {"status_code": exc.code, "json": payload}


def _ebay_token_transport(*, method: str, url: str, headers: dict[str, str], data: str) -> dict[str, Any]:
    request = urllib.request.Request(url=url, data=data.encode("utf-8"), headers=headers, method=method)
    try:
        with urllib.request.urlopen(request, timeout=15) as response:
            return {
                "status_code": response.status,
                "json": json.loads(response.read().decode("utf-8")),
            }
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8")
        try:
            payload = json.loads(raw)
        except ValueError:
            payload = {"message": raw}
        return {"status_code": exc.code, "json": payload}


def _ebay_fixture_path_for_marketplace(marketplace_id: str) -> Path:
    # CONNECT-006: her pazaryerinin kendi örnek verisi olsun ki
    # "farklı marketplace_id -> farklı sonuç" iddiası fixture modda da
    # somut ve tekrar üretilebilir şekilde kanıtlanabilsin (gerçek eBay
    # credential'ı olmadan). EBAY_DE için var olan dosya değişmedi.
    suffix = marketplace_id.removeprefix("EBAY_").lower()
    if suffix and suffix != "de":
        candidate = Path(f"fixtures/ebay/search_response_{suffix}.json")
        if candidate.exists():
            return candidate
    return Path(os.getenv("EBAY_FIXTURE_PATH", "fixtures/ebay/search_response.json"))


def build_ebay_connector(marketplace_id: str | None = None) -> EbayBrowseConnectorService:
    explicit_fixture_mode = os.getenv("EBAY_FIXTURE_MODE", "false").lower() == "true"
    client_id = os.getenv("EBAY_CLIENT_ID", "")
    client_secret = os.getenv("EBAY_CLIENT_SECRET", "")
    has_real_credentials = bool(
        client_id and client_secret and client_id != "CHANGE_ME" and client_secret != "CHANGE_ME"
    )
    fixture_mode = explicit_fixture_mode or not has_real_credentials
    resolved_marketplace_id = marketplace_id or os.getenv("EBAY_MARKETPLACE_ID", "EBAY_DE")

    config = EbayBrowseConfig(
        client_id=client_id,
        client_secret=client_secret,
        marketplace_id=resolved_marketplace_id,
        base_url=os.getenv("EBAY_BASE_URL", "https://api.ebay.com"),
        token_url=os.getenv("EBAY_TOKEN_URL", "https://api.ebay.com/identity/v1/oauth2/token"),
        fixture_mode=fixture_mode,
    )

    if fixture_mode:
        fixture_path = _ebay_fixture_path_for_marketplace(resolved_marketplace_id)
        return EbayBrowseConnectorService(config, http_transport=_fixture_transport(fixture_path))

    return EbayBrowseConnectorService(
        config,
        http_transport=_ebay_http_transport,
        token_transport=_ebay_token_transport,
    )


def configured_ebay_marketplace_ids() -> list[str]:
    # CONNECT-006: eBay'in Browse API'si tek bir base_url + değişen
    # X-EBAY-C-MARKETPLACE-ID header'ıyla çok-ülkeli çalışıyor (kod
    # incelemesiyle doğrulandı, bkz. ADR-008) -- yeni bir connector değil,
    # aynı connector'ın birden çok, farklı marketplace_id'li instance'ı.
    primary = os.getenv("EBAY_MARKETPLACE_ID", "EBAY_DE")
    additional = [
        item.strip()
        for item in os.getenv("EBAY_ADDITIONAL_MARKETPLACES", "").split(",")
        if item.strip()
    ]
    seen: list[str] = []
    for marketplace_id in [primary, *additional]:
        if marketplace_id not in seen:
            seen.append(marketplace_id)
    return seen


def build_ebay_connectors() -> list[EbayBrowseConnectorService]:
    return [build_ebay_connector(marketplace_id=marketplace_id) for marketplace_id in configured_ebay_marketplace_ids()]


def build_idealo_connector() -> IdealoPartnerConnectorService:
    explicit_fixture_mode = os.getenv("IDEALO_FIXTURE_MODE", "false").lower() == "true"
    partner_id = os.getenv("IDEALO_PARTNER_ID", "")
    api_key = os.getenv("IDEALO_API_KEY", "")
    has_real_credentials = bool(
        partner_id and api_key and partner_id != "CHANGE_ME" and api_key != "CHANGE_ME"
    )
    fixture_mode = explicit_fixture_mode or not has_real_credentials

    config = IdealoPartnerConfig(
        partner_id=partner_id,
        api_key=api_key,
        marketplace=os.getenv("IDEALO_MARKETPLACE", "DE"),
        fixture_mode=fixture_mode,
    )
    return IdealoPartnerConnectorService(config)


def idealo_fixture_feed_content() -> str:
    fixture_path = Path(os.getenv("IDEALO_FIXTURE_PATH", "fixtures/idealo/offers.csv"))
    return fixture_path.read_text(encoding="utf-8")


def _bestbuy_http_transport(*, method: str, url: str, headers: dict[str, str]) -> dict[str, Any]:
    request = urllib.request.Request(url=url, headers=headers, method=method)
    try:
        with urllib.request.urlopen(request, timeout=15) as response:
            return {
                "status_code": response.status,
                "json": json.loads(response.read().decode("utf-8")),
            }
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8")
        try:
            payload = json.loads(raw)
        except ValueError:
            payload = {"message": raw}
        return {"status_code": exc.code, "json": payload}


def build_bestbuy_connector() -> BestBuyConnectorService:
    explicit_fixture_mode = os.getenv("BESTBUY_FIXTURE_MODE", "false").lower() == "true"
    api_key = os.getenv("BESTBUY_API_KEY", "")
    has_real_credentials = bool(api_key and api_key != "CHANGE_ME")
    fixture_mode = explicit_fixture_mode or not has_real_credentials

    config = BestBuyConfig(
        api_key=api_key,
        base_url=os.getenv("BESTBUY_BASE_URL", "https://api.bestbuy.com/v1"),
        fixture_mode=fixture_mode,
    )

    if fixture_mode:
        fixture_path = Path(os.getenv("BESTBUY_FIXTURE_PATH", "fixtures/bestbuy/search_response.json"))
        return BestBuyConnectorService(config, http_transport=_fixture_transport(fixture_path))

    return BestBuyConnectorService(config, http_transport=_bestbuy_http_transport)
