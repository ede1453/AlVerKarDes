from __future__ import annotations

import base64
import csv
import io
import json
import time
from copy import deepcopy
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Callable
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse
from uuid import uuid4


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class ConnectorError(RuntimeError):
    def __init__(
        self,
        message: str,
        *,
        code: str,
        retryable: bool = False,
        status_code: int | None = None,
    ):
        super().__init__(message)
        self.code = code
        self.retryable = retryable
        self.status_code = status_code


@dataclass(frozen=True)
class EbayBrowseConfig:
    client_id: str
    client_secret: str
    marketplace_id: str = "EBAY_DE"
    base_url: str = "https://api.ebay.com"
    token_url: str = "https://api.ebay.com/identity/v1/oauth2/token"
    scope: str = "https://api.ebay.com/oauth/api_scope"
    maximum_retries: int = 3
    fixture_mode: bool = False


class EbayBrowseConnectorService:
    def __init__(
        self,
        config: EbayBrowseConfig,
        *,
        http_transport: Callable[..., dict[str, Any]] | None = None,
        token_transport: Callable[..., dict[str, Any]] | None = None,
        sleep: Callable[[float], None] = time.sleep,
    ):
        self.config = config
        self.http_transport = http_transport
        self.token_transport = token_transport
        self.sleep = sleep
        self._token = None
        self._token_expires_at = None
        self._metrics = {
            "request_count": 0,
            "success_count": 0,
            "failure_count": 0,
            "retry_count": 0,
        }

    def validate_configuration(self):
        errors = []
        if not self.config.client_id:
            errors.append("MISSING_CLIENT_ID")
        if not self.config.client_secret:
            errors.append("MISSING_CLIENT_SECRET")
        if not self.config.base_url.startswith("https://"):
            errors.append("BASE_URL_MUST_USE_HTTPS")
        return {"valid": not errors, "errors": errors}

    def build_basic_authorization(self):
        raw = f"{self.config.client_id}:{self.config.client_secret}".encode()
        return "Basic " + base64.b64encode(raw).decode()

    def get_access_token(self):
        expires_after_grace = datetime.now(timezone.utc) + timedelta(seconds=30)
        if self._token and self._token_expires_at and self._token_expires_at > expires_after_grace:
            return {"access_token": self._token, "cached": True}

        if self.config.fixture_mode:
            self._token = "fixture-ebay-token"
            self._token_expires_at = datetime.now(timezone.utc) + timedelta(hours=1)
        else:
            if not self.token_transport:
                raise ConnectorError(
                    "Token transport missing",
                    code="EBAY_TOKEN_TRANSPORT_NOT_CONFIGURED",
                )
            response = self.token_transport(
                method="POST",
                url=self.config.token_url,
                headers={
                    "Authorization": self.build_basic_authorization(),
                    "Content-Type": "application/x-www-form-urlencoded",
                },
                data=urlencode(
                    {
                        "grant_type": "client_credentials",
                        "scope": self.config.scope,
                    }
                ),
            )
            status_code = int(response.get("status_code", 500))
            if status_code >= 400:
                raise ConnectorError(
                    "Token request failed",
                    code="EBAY_TOKEN_REQUEST_FAILED",
                    status_code=status_code,
                )
            data = response.get("json", {})
            self._token = data.get("access_token")
            self._token_expires_at = datetime.now(timezone.utc) + timedelta(
                seconds=int(data.get("expires_in", 7200))
            )
        return {"access_token": self._token, "cached": False}

    def build_headers(self, access_token: str):
        return {
            "Authorization": f"Bearer {access_token}",
            "X-EBAY-C-MARKETPLACE-ID": self.config.marketplace_id,
            "Accept": "application/json",
        }

    def build_search_params(
        self,
        *,
        query: str,
        limit: int = 50,
        offset: int = 0,
        category_ids: list[str] | None = None,
        filters: list[str] | None = None,
        sort: str | None = None,
    ):
        if not query.strip():
            raise ConnectorError("Empty query", code="EBAY_INVALID_QUERY")
        params = {
            "q": query.strip(),
            "limit": min(max(limit, 1), 200),
            "offset": max(offset, 0),
        }
        if category_ids:
            params["category_ids"] = ",".join(category_ids)
        if filters:
            params["filter"] = ",".join(filters)
        if sort:
            params["sort"] = sort
        return params

    def normalize_item_summary(self, raw):
        price = raw.get("price") or {}
        shipping = raw.get("shippingOptions") or []
        shipping_cost = float(((shipping[0].get("shippingCost") or {}).get("value") or 0)) if shipping else 0.0
        value = float(price["value"]) if price.get("value") else None
        return {
            "source": "ebay",
            "marketplace": self.config.marketplace_id,
            "external_id": raw.get("itemId"),
            "title": raw.get("title"),
            "item_url": raw.get("itemWebUrl"),
            "image_url": (raw.get("image") or {}).get("imageUrl"),
            "price": value,
            "currency": price.get("currency"),
            "shipping_cost": shipping_cost,
            "effective_price": value + shipping_cost if value is not None else None,
            "condition": raw.get("condition"),
            "seller": (raw.get("seller") or {}).get("username"),
            "is_real_data": not self.config.fixture_mode,
            "raw": deepcopy(raw),
        }

    def normalize_search_response(self, response):
        items = [self.normalize_item_summary(item) for item in response.get("itemSummaries", [])]
        return {
            "items": items,
            "item_count": len(items),
            "total": int(response.get("total", len(items))),
            "next": response.get("next"),
        }

    def classify_error(self, status_code: int):
        if status_code == 401:
            return ConnectorError("Unauthorized", code="EBAY_UNAUTHORIZED", status_code=status_code)
        if status_code == 403:
            return ConnectorError("Forbidden", code="EBAY_FORBIDDEN", status_code=status_code)
        if status_code == 429:
            return ConnectorError(
                "Rate limited",
                code="EBAY_RATE_LIMITED",
                retryable=True,
                status_code=status_code,
            )
        if status_code >= 500:
            return ConnectorError(
                "Server error",
                code="EBAY_SERVER_ERROR",
                retryable=True,
                status_code=status_code,
            )
        return ConnectorError("Request failed", code="EBAY_REQUEST_FAILED", status_code=status_code)

    def retry_delay(self, attempt_number: int):
        return float(min(2 ** max(attempt_number - 1, 0), 30))

    def execute_get(self, *, path: str, params: dict[str, Any]):
        if not self.http_transport:
            raise ConnectorError("HTTP transport missing", code="EBAY_HTTP_TRANSPORT_NOT_CONFIGURED")
        token = self.get_access_token()["access_token"]
        for attempt in range(1, self.config.maximum_retries + 2):
            self._metrics["request_count"] += 1
            response = self.http_transport(
                method="GET",
                url=self.config.base_url.rstrip("/") + "/" + path.lstrip("/") + "?" + urlencode(params, doseq=True),
                headers=self.build_headers(token),
            )
            status = int(response.get("status_code", 500))
            if status < 400:
                self._metrics["success_count"] += 1
                return {"status_code": status, "data": response.get("json", {}), "attempt_count": attempt}
            error = self.classify_error(status)
            self._metrics["failure_count"] += 1
            if not error.retryable or attempt > self.config.maximum_retries:
                raise error
            self._metrics["retry_count"] += 1
            self.sleep(self.retry_delay(attempt))
        raise ConnectorError("Retry exhausted", code="EBAY_RETRY_EXHAUSTED")

    def search_items(self, **kwargs):
        params = self.build_search_params(**kwargs)
        response = self.execute_get(path="/buy/browse/v1/item_summary/search", params=params)
        return {
            **self.normalize_search_response(response["data"]),
            "attempt_count": response["attempt_count"],
        }

    def get_item(self, *, item_id: str):
        response = self.execute_get(path=f"/buy/browse/v1/item/{item_id}", params={})
        return {"item": self.normalize_item_summary(response["data"])}

    def build_price_snapshots(self, items):
        rows = [
            {
                "snapshot_id": str(uuid4()),
                "source": "ebay",
                "external_id": item.get("external_id"),
                "price": item.get("price"),
                "shipping_cost": item.get("shipping_cost", 0),
                "effective_price": item.get("effective_price"),
                "currency": item.get("currency"),
                "observed_at": now_iso(),
                "is_real_data": not self.config.fixture_mode,
            }
            for item in items
            if item.get("price") is not None
        ]
        return {"snapshot_count": len(rows), "snapshots": rows}

    def validate_affiliate_url(self, url: str | None):
        value = (url or "").lower()
        return {"valid": bool(value) and any(key in value for key in ("campid=", "customid=", "mkevt="))}

    def deduplicate_items(self, items):
        seen = set()
        output = []
        for item in items:
            key = item.get("external_id") or item.get("item_url")
            if not key or key in seen:
                continue
            seen.add(key)
            output.append(item)
        return {"input_count": len(items), "output_count": len(output), "items": output}

    def build_ingestion_records(self, items):
        rows = [
            {
                "source": "ebay",
                "marketplace": self.config.marketplace_id,
                "external_id": item.get("external_id"),
                "title": item.get("title"),
                "url": item.get("item_url"),
                "price": item.get("price"),
                "currency": item.get("currency"),
                "collected_at": now_iso(),
                "is_real_data": not self.config.fixture_mode,
            }
            for item in items
        ]
        return {"record_count": len(rows), "records": rows}

    def metrics(self):
        request_count = self._metrics["request_count"]
        return {
            **self._metrics,
            "success_rate": round(self._metrics["success_count"] / request_count, 4) if request_count else 0.0,
        }

    def health_check(self):
        validation = self.validate_configuration()
        return {
            "healthy": validation["valid"],
            "connector": "ebay-browse-api",
            "marketplace": self.config.marketplace_id,
            "fixture_mode": self.config.fixture_mode,
            "errors": validation["errors"],
            "checked_at": now_iso(),
        }

    def run_collection(self, *, query: str, limit: int = 50):
        search = self.search_items(query=query, limit=limit)
        deduplicated = self.deduplicate_items(search["items"])
        snapshots = self.build_price_snapshots(deduplicated["items"])
        records = self.build_ingestion_records(deduplicated["items"])
        return {
            "executed": True,
            "connector": "ebay-browse-api",
            "item_count": deduplicated["output_count"],
            "snapshot_count": snapshots["snapshot_count"],
            "records": records["records"],
            "price_snapshots": snapshots["snapshots"],
            "is_real_data": not self.config.fixture_mode,
        }

    def readiness(self):
        health = self.health_check()
        return {
            "ready": health["healthy"],
            "buy_api_access_may_require_approval": True,
        }


@dataclass(frozen=True)
class IdealoPartnerConfig:
    partner_id: str
    api_key: str
    marketplace: str = "DE"
    fixture_mode: bool = False


class IdealoPartnerConnectorService:
    def __init__(self, config: IdealoPartnerConfig):
        self.config = config

    def validate_configuration(self):
        errors = []
        if not self.config.partner_id:
            errors.append("MISSING_PARTNER_ID")
        if not self.config.api_key:
            errors.append("MISSING_API_KEY")
        return {"valid": not errors, "errors": errors}

    def parse_csv_feed(self, content: str, delimiter: str = ","):
        rows = [dict(row) for row in csv.DictReader(io.StringIO(content), delimiter=delimiter)]
        return {"row_count": len(rows), "rows": rows}

    def parse_json_feed(self, content: str):
        payload = json.loads(content)
        rows = payload if isinstance(payload, list) else payload.get("offers", [])
        return {"row_count": len(rows), "rows": rows}

    def normalize_offer(self, raw):
        raw_price = raw.get("price") or raw.get("Price")
        raw_shipping = raw.get("shipping") or raw.get("shippingCosts") or 0
        price = float(raw_price) if raw_price not in (None, "") else None
        shipping = float(raw_shipping) if raw_shipping not in (None, "") else 0.0
        return {
            "source": "idealo",
            "marketplace": self.config.marketplace,
            "external_id": raw.get("offerId") or raw.get("sku") or raw.get("id"),
            "title": raw.get("title") or raw.get("name"),
            "brand": raw.get("brand"),
            "gtin": raw.get("gtin") or raw.get("ean"),
            "url": raw.get("url") or raw.get("deeplink"),
            "price": price,
            "shipping_cost": shipping,
            "effective_price": price + shipping if price is not None else None,
            "currency": raw.get("currency") or "EUR",
            "availability": raw.get("availability"),
            "observed_at": now_iso(),
            "is_real_data": not self.config.fixture_mode,
        }

    def validate_offer(self, offer):
        errors = []
        if not offer.get("external_id"):
            errors.append("MISSING_EXTERNAL_ID")
        if not offer.get("title"):
            errors.append("MISSING_TITLE")
        if offer.get("price") is None or offer.get("price", 0) <= 0:
            errors.append("INVALID_PRICE")
        if not offer.get("url"):
            errors.append("MISSING_URL")
        return {"valid": not errors, "errors": errors}

    def normalize_feed(self, rows):
        accepted = []
        rejected = []
        for row in rows:
            offer = self.normalize_offer(row)
            validation = self.validate_offer(offer)
            if validation["valid"]:
                accepted.append(offer)
            else:
                rejected.append({"raw": row, "errors": validation["errors"]})
        return {
            "accepted_count": len(accepted),
            "rejected_count": len(rejected),
            "offers": accepted,
            "rejected": rejected,
        }

    def deduplicate_offers(self, offers):
        seen = set()
        output = []
        for offer in offers:
            key = (offer.get("external_id"), offer.get("effective_price"), offer.get("currency"))
            if key in seen:
                continue
            seen.add(key)
            output.append(offer)
        return {"input_count": len(offers), "output_count": len(output), "offers": output}

    def build_price_snapshots(self, offers):
        rows = [
            {
                "snapshot_id": str(uuid4()),
                "source": "idealo",
                "external_id": offer.get("external_id"),
                "price": offer.get("price"),
                "shipping_cost": offer.get("shipping_cost"),
                "effective_price": offer.get("effective_price"),
                "currency": offer.get("currency"),
                "observed_at": offer.get("observed_at") or now_iso(),
                "is_real_data": not self.config.fixture_mode,
            }
            for offer in offers
            if offer.get("price") is not None
        ]
        return {"snapshot_count": len(rows), "snapshots": rows}

    def run_feed_collection(self, *, content: str, format: str = "csv", delimiter: str = ","):
        if format.lower() == "json":
            parsed = self.parse_json_feed(content)
        else:
            parsed = self.parse_csv_feed(content, delimiter)
        normalized = self.normalize_feed(parsed["rows"])
        deduplicated = self.deduplicate_offers(normalized["offers"])
        snapshots = self.build_price_snapshots(deduplicated["offers"])
        return {
            "executed": True,
            "connector": "idealo-partner-feed",
            "offer_count": deduplicated["output_count"],
            "rejected_count": normalized["rejected_count"],
            "offers": deduplicated["offers"],
            "price_snapshots": snapshots["snapshots"],
            "is_real_data": not self.config.fixture_mode,
        }

    def health_check(self):
        validation = self.validate_configuration()
        return {
            "healthy": validation["valid"],
            "connector": "idealo-partner-feed",
            "fixture_mode": self.config.fixture_mode,
            "errors": validation["errors"],
            "supported_modes": ["csv", "txt", "xml-adapter", "json", "partner-api"],
            "checked_at": now_iso(),
        }


@dataclass(frozen=True)
class BestBuyConfig:
    api_key: str
    base_url: str = "https://api.bestbuy.com/v1"
    maximum_retries: int = 3
    fixture_mode: bool = False


class BestBuyConnectorService:
    # CONNECT-006 (ADR-008): Best Buy Products API -- basit apiKey
    # query-param kimlik dogrulamasi kullaniyor (eBay'in OAuth2
    # client-credentials akisinin aksine, token fetch adimi yok).
    def __init__(
        self,
        config: BestBuyConfig,
        *,
        http_transport: Callable[..., dict[str, Any]] | None = None,
        sleep: Callable[[float], None] = time.sleep,
    ):
        self.config = config
        self.http_transport = http_transport
        self.sleep = sleep
        self._metrics = {
            "request_count": 0,
            "success_count": 0,
            "failure_count": 0,
            "retry_count": 0,
        }

    def validate_configuration(self):
        errors = []
        if not self.config.api_key:
            errors.append("MISSING_API_KEY")
        if not self.config.base_url.startswith("https://"):
            errors.append("BASE_URL_MUST_USE_HTTPS")
        return {"valid": not errors, "errors": errors}

    def build_search_path(self, keywords: str) -> str:
        if not keywords.strip():
            raise ConnectorError("Empty keywords", code="BESTBUY_INVALID_QUERY")
        from urllib.parse import quote_plus

        return f"/products(search={quote_plus(keywords.strip())})"

    def build_search_params(self, *, page_size: int = 10):
        return {
            "format": "json",
            "apiKey": self.config.api_key,
            "pageSize": min(max(page_size, 1), 100),
            "show": "sku,name,salePrice,regularPrice,url,onlineAvailability,image",
        }

    def normalize_product(self, raw):
        sku = raw.get("sku")
        return {
            "source": "bestbuy",
            "is_real_data": not self.config.fixture_mode,
            # Best Buy'in gercek API'si sku'yu integer donuyor
            # (canli testte bulundu) -- OfferCreate.store_sku str bekliyor.
            "external_id": str(sku) if sku is not None else None,
            "title": raw.get("name"),
            "price": raw.get("salePrice") if raw.get("salePrice") is not None else raw.get("regularPrice"),
            "regular_price": raw.get("regularPrice"),
            "currency": "USD",
            "url": raw.get("url"),
            "image_url": raw.get("image"),
            "availability": "IN_STOCK" if raw.get("onlineAvailability") else "OUT_OF_STOCK",
            "raw": deepcopy(raw),
        }

    def normalize_search_response(self, response):
        raw_items = response.get("products", [])
        items = [self.normalize_product(item) for item in raw_items]
        return {
            "items": items,
            "item_count": len(items),
            "total": int(response.get("total", len(items))),
        }

    def classify_error(self, status_code: int):
        if status_code == 400:
            return ConnectorError("Malformed request", code="BESTBUY_BAD_REQUEST", status_code=status_code)
        if status_code == 403:
            return ConnectorError(
                "Invalid API key or rate limit exceeded",
                code="BESTBUY_FORBIDDEN",
                status_code=status_code,
            )
        if status_code == 404:
            return ConnectorError("Not found", code="BESTBUY_NOT_FOUND", status_code=status_code)
        if status_code >= 500:
            return ConnectorError(
                "Server error",
                code="BESTBUY_SERVER_ERROR",
                retryable=True,
                status_code=status_code,
            )
        return ConnectorError("Request failed", code="BESTBUY_REQUEST_FAILED", status_code=status_code)

    def retry_delay(self, attempt_number: int):
        return float(min(2 ** max(attempt_number - 1, 0), 30))

    def execute_get(self, *, path: str, params: dict[str, Any]):
        if not self.http_transport:
            raise ConnectorError("HTTP transport missing", code="BESTBUY_HTTP_TRANSPORT_NOT_CONFIGURED")
        for attempt in range(1, self.config.maximum_retries + 2):
            self._metrics["request_count"] += 1
            response = self.http_transport(
                method="GET",
                url=self.config.base_url.rstrip("/") + path + "?" + urlencode(params),
                headers={"Accept": "application/json"},
            )
            status = int(response.get("status_code", 500))
            if status < 400:
                self._metrics["success_count"] += 1
                return {"status_code": status, "data": response.get("json", {}), "attempt_count": attempt}
            error = self.classify_error(status)
            self._metrics["failure_count"] += 1
            if not error.retryable or attempt > self.config.maximum_retries:
                raise error
            self._metrics["retry_count"] += 1
            self.sleep(self.retry_delay(attempt))
        raise ConnectorError("Retry exhausted", code="BESTBUY_RETRY_EXHAUSTED")

    def search_products(self, *, keywords: str, page_size: int = 10):
        path = self.build_search_path(keywords)
        params = self.build_search_params(page_size=page_size)
        response = self.execute_get(path=path, params=params)
        return {
            **self.normalize_search_response(response["data"]),
            "attempt_count": response["attempt_count"],
        }

    def metrics(self):
        request_count = self._metrics["request_count"]
        return {
            **self._metrics,
            "success_rate": round(self._metrics["success_count"] / request_count, 4) if request_count else 0.0,
        }

    def health_check(self):
        validation = self.validate_configuration()
        return {
            "healthy": validation["valid"],
            "connector": "bestbuy-products-api",
            "fixture_mode": self.config.fixture_mode,
            "errors": validation["errors"],
            "checked_at": now_iso(),
        }


@dataclass(frozen=True)
class AffiliateConfig:
    network: str
    publisher_id: str
    campaign_id: str
    allowed_domains: tuple[str, ...]


class AffiliateAttributionService:
    def __init__(self, config: AffiliateConfig):
        self.config = config
        self._clicks = {}
        self._conversions = []

    def validate_configuration(self):
        errors = []
        if not self.config.network:
            errors.append("MISSING_NETWORK")
        if not self.config.publisher_id:
            errors.append("MISSING_PUBLISHER_ID")
        if not self.config.campaign_id:
            errors.append("MISSING_CAMPAIGN_ID")
        return {"valid": not errors, "errors": errors}

    def build_tracking_url(self, *, destination_url: str, sub_id: str | None = None):
        parsed = urlparse(destination_url)
        if parsed.hostname not in self.config.allowed_domains:
            raise ConnectorError("Domain not allowed", code="AFFILIATE_DOMAIN_NOT_ALLOWED")
        query = dict(parse_qsl(parsed.query, keep_blank_values=True))
        query.update(
            {
                "publisher_id": self.config.publisher_id,
                "campaign_id": self.config.campaign_id,
            }
        )
        if sub_id:
            query["sub_id"] = sub_id
        return {
            "url": urlunparse(parsed._replace(query=urlencode(query))),
            "network": self.config.network,
        }

    def record_click(self, *, user_id: str, deal_id: str, destination_url: str):
        click_id = str(uuid4())
        tracked = self.build_tracking_url(destination_url=destination_url, sub_id=click_id)
        item = {
            "click_id": click_id,
            "user_id": user_id,
            "deal_id": deal_id,
            "tracked_url": tracked["url"],
            "network": self.config.network,
            "clicked_at": now_iso(),
        }
        self._clicks[click_id] = item
        return {"recorded": True, "click": deepcopy(item)}

    def record_conversion(self, *, click_id: str, order_value: float, commission_value: float, external_order_id: str):
        if click_id not in self._clicks:
            return {"recorded": False, "reason": "CLICK_NOT_FOUND"}
        if not self.prevent_duplicate_conversion(external_order_id)["allowed"]:
            return {"recorded": False, "reason": "DUPLICATE_CONVERSION"}
        item = {
            "conversion_id": str(uuid4()),
            "click_id": click_id,
            "external_order_id": external_order_id,
            "order_value": float(order_value),
            "commission_value": float(commission_value),
            "network": self.config.network,
            "converted_at": now_iso(),
        }
        self._conversions.append(item)
        return {"recorded": True, "conversion": deepcopy(item)}

    def prevent_duplicate_conversion(self, external_order_id: str):
        duplicate = any(item["external_order_id"] == external_order_id for item in self._conversions)
        return {"allowed": not duplicate, "duplicate": duplicate}

    def calculate_conversion_rate(self):
        clicks = len(self._clicks)
        conversions = len(self._conversions)
        return {
            "click_count": clicks,
            "conversion_count": conversions,
            "conversion_rate": round(conversions / clicks, 4) if clicks else 0.0,
        }

    def calculate_revenue(self):
        return {
            "commission_revenue": round(sum(item["commission_value"] for item in self._conversions), 2),
            "attributed_order_value": round(sum(item["order_value"] for item in self._conversions), 2),
        }

    def disclosure(self):
        return {
            "required": True,
            "text": "Bu baglanti uzerinden yapilan uygun alisverislerden komisyon kazanilabilir.",
            "ranking_independence_required": True,
        }

    def audit(self):
        return {
            "network": self.config.network,
            "click_count": len(self._clicks),
            "conversion_count": len(self._conversions),
            "disclosure": self.disclosure(),
            "audited_at": now_iso(),
        }

    def readiness(self):
        validation = self.validate_configuration()
        return {
            "ready": validation["valid"],
            "network": self.config.network,
            "errors": validation["errors"],
            "trust_controls": {
                "disclosure_required": True,
                "sponsored_separation_required": True,
                "ranking_must_be_commission_independent": True,
            },
        }
