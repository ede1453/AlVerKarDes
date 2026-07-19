from __future__ import annotations

import json
import random
import time
from copy import deepcopy
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from hashlib import sha256
from typing import Any, Callable
from uuid import uuid4


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


def now_iso() -> str:
    return now_utc().isoformat()


@dataclass(frozen=True)
class AmazonCreatorsConfig:
    base_url: str
    marketplace: str
    partner_tag: str
    client_id: str
    client_secret: str
    timeout_seconds: float = 15.0
    maximum_retries: int = 3
    cache_ttl_seconds: int = 300
    requests_per_second: float = 1.0
    fixture_mode: bool = False


class AmazonConnectorError(RuntimeError):
    def __init__(
        self,
        message: str,
        *,
        code: str = "AMAZON_CONNECTOR_ERROR",
        retryable: bool = False,
        status_code: int | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.retryable = retryable
        self.status_code = status_code
        self.details = details or {}

    def to_dict(self) -> dict[str, Any]:
        return {
            "code": self.code,
            "message": str(self),
            "retryable": self.retryable,
            "status_code": self.status_code,
            "details": deepcopy(self.details),
        }


class InMemoryTokenProvider:
    def __init__(self) -> None:
        self._token: str | None = None
        self._expires_at: datetime | None = None

    def get_token(
        self,
        *,
        client_id: str,
        client_secret: str,
        fetcher: Callable[[str, str], dict[str, Any]],
    ) -> dict[str, Any]:
        if (
            self._token
            and self._expires_at
            and self._expires_at
            > now_utc() + timedelta(seconds=30)
        ):
            return {
                "access_token": self._token,
                "cached": True,
                "expires_at": self._expires_at.isoformat(),
            }

        payload = fetcher(client_id, client_secret)
        token = str(payload.get("access_token", "")).strip()
        expires_in = int(payload.get("expires_in", 3600))

        if not token:
            raise AmazonConnectorError(
                "Amazon access token response did not include access_token.",
                code="TOKEN_RESPONSE_INVALID",
            )

        self._token = token
        self._expires_at = now_utc() + timedelta(
            seconds=max(expires_in, 60)
        )

        return {
            "access_token": token,
            "cached": False,
            "expires_at": self._expires_at.isoformat(),
        }


class SlidingRateLimiter:
    def __init__(self) -> None:
        self._last_request_at: datetime | None = None

    def acquire(
        self,
        *,
        requests_per_second: float,
        sleep: Callable[[float], None] = time.sleep,
    ) -> dict[str, Any]:
        rps = max(float(requests_per_second), 0.01)
        minimum_interval = 1.0 / rps
        waited = 0.0

        if self._last_request_at is not None:
            elapsed = (
                now_utc() - self._last_request_at
            ).total_seconds()
            waited = max(minimum_interval - elapsed, 0.0)

            if waited > 0:
                sleep(waited)

        self._last_request_at = now_utc()

        return {
            "acquired": True,
            "waited_seconds": round(waited, 4),
            "requests_per_second": rps,
        }


class ResponseCache:
    def __init__(self) -> None:
        self._items: dict[str, dict[str, Any]] = {}

    def _key(
        self,
        operation: str,
        payload: dict[str, Any],
    ) -> str:
        serialized = json.dumps(
            payload,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        )
        return sha256(
            f"{operation}:{serialized}".encode("utf-8")
        ).hexdigest()

    def get(
        self,
        *,
        operation: str,
        payload: dict[str, Any],
    ) -> dict[str, Any] | None:
        key = self._key(operation, payload)
        item = self._items.get(key)

        if item is None:
            return None

        if datetime.fromisoformat(item["expires_at"]) <= now_utc():
            self._items.pop(key, None)
            return None

        return deepcopy(item["value"])

    def put(
        self,
        *,
        operation: str,
        payload: dict[str, Any],
        value: dict[str, Any],
        ttl_seconds: int,
    ) -> None:
        key = self._key(operation, payload)
        self._items[key] = {
            "value": deepcopy(value),
            "expires_at": (
                now_utc()
                + timedelta(seconds=max(ttl_seconds, 1))
            ).isoformat(),
        }


class AmazonCreatorsConnectorService:
    """
    Amazon Creators API connector.

    The exact resource paths are configuration-driven because Amazon's
    Creators API documentation and account enablement may vary by marketplace
    and onboarding state. No deprecated PA-API request signing is used.
    """

    def __init__(
        self,
        config: AmazonCreatorsConfig,
        *,
        token_provider: InMemoryTokenProvider | None = None,
        rate_limiter: SlidingRateLimiter | None = None,
        cache: ResponseCache | None = None,
        http_transport: Callable[..., dict[str, Any]] | None = None,
        token_fetcher: Callable[[str, str], dict[str, Any]] | None = None,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        self.config = config
        self.token_provider = token_provider or InMemoryTokenProvider()
        self.rate_limiter = rate_limiter or SlidingRateLimiter()
        self.cache = cache or ResponseCache()
        self.http_transport = http_transport
        self.token_fetcher = token_fetcher
        self.sleep = sleep
        self._metrics = {
            "request_count": 0,
            "success_count": 0,
            "failure_count": 0,
            "cache_hit_count": 0,
            "retry_count": 0,
        }
        self._last_health: dict[str, Any] | None = None

    # RC341
    def validate_configuration(self) -> dict[str, Any]:
        errors = []

        if not self.config.base_url.startswith("https://"):
            errors.append("BASE_URL_MUST_USE_HTTPS")

        for field_name in [
            "marketplace",
            "partner_tag",
            "client_id",
            "client_secret",
        ]:
            if not str(
                getattr(self.config, field_name)
            ).strip():
                errors.append(
                    f"MISSING_{field_name.upper()}"
                )

        return {
            "valid": not errors,
            "errors": errors,
            "marketplace": self.config.marketplace,
            "fixture_mode": self.config.fixture_mode,
        }

    # RC342
    def get_access_token(self) -> dict[str, Any]:
        if self.config.fixture_mode:
            return {
                "access_token": "fixture-token",
                "cached": True,
                "expires_at": (
                    now_utc() + timedelta(hours=1)
                ).isoformat(),
            }

        if self.token_fetcher is None:
            raise AmazonConnectorError(
                "No Amazon token fetcher is configured.",
                code="TOKEN_FETCHER_NOT_CONFIGURED",
            )

        return self.token_provider.get_token(
            client_id=self.config.client_id,
            client_secret=self.config.client_secret,
            fetcher=self.token_fetcher,
        )

    # RC343
    def build_headers(
        self,
        *,
        access_token: str,
        correlation_id: str | None = None,
    ) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {access_token}",
            "Accept": "application/json",
            "Content-Type": "application/json",
            "User-Agent": "AI-Consumer-Intelligence/1.0",
            "X-Correlation-ID": (
                correlation_id or str(uuid4())
            ),
        }

    # RC344
    def build_search_request(
        self,
        *,
        keywords: str,
        page_size: int = 10,
        page_token: str | None = None,
        filters: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        clean_keywords = keywords.strip()

        if not clean_keywords:
            raise AmazonConnectorError(
                "Search keywords cannot be empty.",
                code="INVALID_SEARCH_KEYWORDS",
            )

        payload = {
            "keywords": clean_keywords,
            "marketplace": self.config.marketplace,
            "partnerTag": self.config.partner_tag,
            "pageSize": min(max(page_size, 1), 50),
            "filters": filters or {},
        }

        if page_token:
            payload["pageToken"] = page_token

        return payload

    # RC345
    def build_item_request(
        self,
        *,
        identifiers: list[str],
    ) -> dict[str, Any]:
        cleaned = [
            str(item).strip()
            for item in identifiers
            if str(item).strip()
        ]

        if not cleaned:
            raise AmazonConnectorError(
                "At least one Amazon product identifier is required.",
                code="MISSING_PRODUCT_IDENTIFIER",
            )

        return {
            "identifiers": cleaned[:10],
            "marketplace": self.config.marketplace,
            "partnerTag": self.config.partner_tag,
        }

    # RC346
    def normalize_product(
        self,
        raw: dict[str, Any],
    ) -> dict[str, Any]:
        identifier = (
            raw.get("asin")
            or raw.get("id")
            or raw.get("identifier")
        )

        return {
            "source": "amazon",
            # CONNECT-004 (Amazon deferred to VISION-0xx -- see ADR-003
            # Sonuc Raporu): every product/offer/snapshot this connector
            # produces is explicitly tagged so no consumer can mistake
            # test-fixture data for a real Amazon listing.
            "is_real_data": not self.config.fixture_mode,
            "marketplace": self.config.marketplace,
            "external_id": identifier,
            "asin": identifier,
            "title": (
                raw.get("title")
                or raw.get("name")
                or ""
            ),
            "brand": raw.get("brand"),
            "detail_page_url": (
                raw.get("detailPageUrl")
                or raw.get("url")
            ),
            "image_url": (
                raw.get("imageUrl")
                or raw.get("primaryImage")
            ),
            "categories": raw.get("categories", []),
            "raw": deepcopy(raw),
        }

    # RC347
    def normalize_offer(
        self,
        *,
        product: dict[str, Any],
        raw_offer: dict[str, Any],
    ) -> dict[str, Any]:
        amount = (
            raw_offer.get("amount")
            or raw_offer.get("price")
            or raw_offer.get(
                "displayAmountValue"
            )
        )

        currency = (
            raw_offer.get("currency")
            or raw_offer.get("currencyCode")
            or "EUR"
        )

        return {
            "source": "amazon",
            "is_real_data": not self.config.fixture_mode,
            "marketplace": self.config.marketplace,
            "external_product_id": product.get(
                "external_id"
            ),
            "price": (
                float(amount)
                if amount is not None
                else None
            ),
            "currency": currency,
            "availability": (
                raw_offer.get("availability")
                or raw_offer.get("availabilityMessage")
            ),
            "merchant": (
                raw_offer.get("merchant")
                or raw_offer.get("seller")
            ),
            "condition": raw_offer.get("condition"),
            "is_prime": bool(
                raw_offer.get("isPrime")
                or raw_offer.get("primeEligible")
            ),
            "is_amazon_fulfilled": bool(
                raw_offer.get("isAmazonFulfilled")
            ),
            "observed_at": now_iso(),
            "raw": deepcopy(raw_offer),
        }

    # RC348
    def normalize_items_response(
        self,
        response: dict[str, Any],
    ) -> dict[str, Any]:
        raw_items = (
            response.get("items")
            or response.get("products")
            or response.get(
                "ItemsResult",
                {},
            ).get("Items")
            or []
        )

        products = []

        for raw in raw_items:
            product = self.normalize_product(raw)
            offers = (
                raw.get("offers")
                or raw.get("Offers", {}).get("Listings")
                or []
            )
            product["offers"] = [
                self.normalize_offer(
                    product=product,
                    raw_offer=offer,
                )
                for offer in offers
            ]
            products.append(product)

        return {
            "items": products,
            "item_count": len(products),
            "next_page_token": (
                response.get("nextPageToken")
                or response.get("next_page_token")
            ),
        }

    # RC349
    def classify_error(
        self,
        *,
        status_code: int,
        payload: dict[str, Any] | None = None,
    ) -> AmazonConnectorError:
        data = payload or {}

        if status_code == 401:
            return AmazonConnectorError(
                "Amazon authentication failed.",
                code="AMAZON_UNAUTHORIZED",
                retryable=False,
                status_code=status_code,
                details=data,
            )

        if status_code == 403:
            return AmazonConnectorError(
                "Amazon account is not authorized for this resource.",
                code="AMAZON_FORBIDDEN",
                retryable=False,
                status_code=status_code,
                details=data,
            )

        if status_code == 429:
            return AmazonConnectorError(
                "Amazon request was throttled.",
                code="AMAZON_RATE_LIMITED",
                retryable=True,
                status_code=status_code,
                details=data,
            )

        if status_code >= 500:
            return AmazonConnectorError(
                "Amazon service returned a server error.",
                code="AMAZON_SERVER_ERROR",
                retryable=True,
                status_code=status_code,
                details=data,
            )

        return AmazonConnectorError(
            "Amazon request failed.",
            code="AMAZON_REQUEST_FAILED",
            retryable=False,
            status_code=status_code,
            details=data,
        )

    # RC350
    def retry_delay(
        self,
        *,
        attempt_number: int,
        retry_after_seconds: float | None = None,
    ) -> float:
        if retry_after_seconds is not None:
            return max(float(retry_after_seconds), 0.0)

        exponential = min(
            2 ** max(attempt_number - 1, 0),
            30,
        )
        jitter = random.uniform(0, 0.25)
        return round(exponential + jitter, 3)

    # RC351
    def execute(
        self,
        *,
        operation: str,
        method: str,
        path: str,
        payload: dict[str, Any],
        cacheable: bool = True,
    ) -> dict[str, Any]:
        cached = (
            self.cache.get(
                operation=operation,
                payload=payload,
            )
            if cacheable
            else None
        )

        if cached is not None:
            self._metrics["cache_hit_count"] += 1
            return {
                **cached,
                "cache_hit": True,
            }

        if self.http_transport is None:
            raise AmazonConnectorError(
                "No Amazon HTTP transport is configured.",
                code="HTTP_TRANSPORT_NOT_CONFIGURED",
            )

        token = self.get_access_token()[
            "access_token"
        ]

        last_error: AmazonConnectorError | None = None

        for attempt in range(
            1,
            self.config.maximum_retries + 2,
        ):
            self.rate_limiter.acquire(
                requests_per_second=(
                    self.config.requests_per_second
                ),
                sleep=self.sleep,
            )

            self._metrics["request_count"] += 1

            try:
                response = self.http_transport(
                    method=method,
                    url=(
                        self.config.base_url.rstrip("/")
                        + "/"
                        + path.lstrip("/")
                    ),
                    headers=self.build_headers(
                        access_token=token
                    ),
                    json=payload,
                    timeout=self.config.timeout_seconds,
                )

                status_code = int(
                    response.get("status_code", 200)
                )
                body = response.get("json", {})

                if status_code >= 400:
                    raise self.classify_error(
                        status_code=status_code,
                        payload=body,
                    )

                result = {
                    "status_code": status_code,
                    "data": body,
                    "cache_hit": False,
                    "attempt_count": attempt,
                }

                if cacheable:
                    self.cache.put(
                        operation=operation,
                        payload=payload,
                        value=result,
                        ttl_seconds=(
                            self.config.cache_ttl_seconds
                        ),
                    )

                self._metrics["success_count"] += 1
                return result

            except AmazonConnectorError as exc:
                self._metrics["failure_count"] += 1
                last_error = exc

                if (
                    not exc.retryable
                    or attempt
                    > self.config.maximum_retries
                ):
                    raise

                self._metrics["retry_count"] += 1
                delay = self.retry_delay(
                    attempt_number=attempt,
                    retry_after_seconds=(
                        exc.details.get(
                            "retry_after_seconds"
                        )
                    ),
                )
                self.sleep(delay)

        assert last_error is not None
        raise last_error

    # RC352
    def search_products(
        self,
        *,
        keywords: str,
        page_size: int = 10,
        page_token: str | None = None,
        filters: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        payload = self.build_search_request(
            keywords=keywords,
            page_size=page_size,
            page_token=page_token,
            filters=filters,
        )

        result = self.execute(
            operation="search_products",
            method="POST",
            path="/products/search",
            payload=payload,
            cacheable=True,
        )

        normalized = self.normalize_items_response(
            result["data"]
        )

        return {
            **normalized,
            "cache_hit": result["cache_hit"],
            "attempt_count": result["attempt_count"],
        }

    # RC353
    def get_products(
        self,
        *,
        identifiers: list[str],
    ) -> dict[str, Any]:
        payload = self.build_item_request(
            identifiers=identifiers
        )

        result = self.execute(
            operation="get_products",
            method="POST",
            path="/products/items",
            payload=payload,
            cacheable=True,
        )

        normalized = self.normalize_items_response(
            result["data"]
        )

        return {
            **normalized,
            "cache_hit": result["cache_hit"],
            "attempt_count": result["attempt_count"],
        }

    # RC354
    def collect_price_snapshots(
        self,
        *,
        products: list[dict[str, Any]],
    ) -> dict[str, Any]:
        snapshots = []

        for product in products:
            for offer in product.get("offers", []):
                if offer.get("price") is None:
                    continue

                snapshots.append(
                    {
                        "snapshot_id": str(uuid4()),
                        "source": "amazon",
                        "is_real_data": not self.config.fixture_mode,
                        "external_product_id": (
                            product.get("external_id")
                        ),
                        "price": offer["price"],
                        "currency": offer["currency"],
                        "availability": offer.get(
                            "availability"
                        ),
                        "merchant": offer.get("merchant"),
                        "observed_at": offer.get(
                            "observed_at"
                        )
                        or now_iso(),
                    }
                )

        return {
            "snapshot_count": len(snapshots),
            "snapshots": snapshots,
        }

    # RC355
    def deduplicate_products(
        self,
        *,
        products: list[dict[str, Any]],
    ) -> dict[str, Any]:
        seen = set()
        deduplicated = []

        for product in products:
            key = (
                product.get("asin")
                or product.get("external_id")
                or product.get("detail_page_url")
            )

            if not key or key in seen:
                continue

            seen.add(key)
            deduplicated.append(product)

        return {
            "input_count": len(products),
            "output_count": len(deduplicated),
            "products": deduplicated,
        }

    # RC356
    def validate_attribution(
        self,
        *,
        detail_page_url: str | None,
    ) -> dict[str, Any]:
        url = detail_page_url or ""
        valid = (
            bool(url)
            and (
                self.config.partner_tag in url
                or "tag=" in url
                or "ascsubtag=" in url
            )
        )

        return {
            "valid": valid,
            "detail_page_url": detail_page_url,
            "partner_tag": self.config.partner_tag,
        }

    # RC357
    def build_ingestion_records(
        self,
        *,
        products: list[dict[str, Any]],
    ) -> dict[str, Any]:
        records = []

        for product in products:
            records.append(
                {
                    "source": "amazon",
                    "is_real_data": not self.config.fixture_mode,
                    "marketplace": self.config.marketplace,
                    "external_id": product.get(
                        "external_id"
                    ),
                    "title": product.get("title"),
                    "brand": product.get("brand"),
                    "url": product.get(
                        "detail_page_url"
                    ),
                    "image_url": product.get(
                        "image_url"
                    ),
                    "offers": deepcopy(
                        product.get("offers", [])
                    ),
                    "collected_at": now_iso(),
                }
            )

        return {
            "record_count": len(records),
            "records": records,
        }

    # RC358
    def metrics(self) -> dict[str, Any]:
        requests = self._metrics["request_count"]
        successes = self._metrics["success_count"]

        return {
            **deepcopy(self._metrics),
            "success_rate": (
                round(successes / requests, 4)
                if requests
                else 0.0
            ),
        }

    # RC359
    def health_check(self) -> dict[str, Any]:
        config_check = self.validate_configuration()

        healthy = config_check["valid"]

        self._last_health = {
            "healthy": healthy,
            "connector": "amazon-creators-api",
            "marketplace": self.config.marketplace,
            "fixture_mode": self.config.fixture_mode,
            "checked_at": now_iso(),
            "errors": config_check["errors"],
        }

        return deepcopy(self._last_health)

    # RC360
    def run_collection(
        self,
        *,
        keywords: str,
        page_size: int = 10,
        filters: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        started_at = now_iso()
        search_result = self.search_products(
            keywords=keywords,
            page_size=page_size,
            filters=filters,
        )

        deduplicated = self.deduplicate_products(
            products=search_result["items"]
        )

        snapshots = self.collect_price_snapshots(
            products=deduplicated["products"]
        )

        ingestion = self.build_ingestion_records(
            products=deduplicated["products"]
        )

        return {
            "executed": True,
            "connector": "amazon-creators-api",
            "is_real_data": not self.config.fixture_mode,
            "started_at": started_at,
            "completed_at": now_iso(),
            "item_count": deduplicated[
                "output_count"
            ],
            "snapshot_count": snapshots[
                "snapshot_count"
            ],
            "records": ingestion["records"],
            "price_snapshots": snapshots["snapshots"],
            "cache_hit": search_result["cache_hit"],
            "attempt_count": search_result[
                "attempt_count"
            ],
            "metrics": self.metrics(),
        }
