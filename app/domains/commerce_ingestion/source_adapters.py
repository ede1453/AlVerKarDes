from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class SourceAdapterError(RuntimeError):
    pass


class BaseSourceAdapter:
    source_name = "base"

    def collect(self, source_config: dict[str, Any]) -> list[dict[str, Any]]:
        raise NotImplementedError


class FixtureJSONSourceAdapter(BaseSourceAdapter):
    source_name = "fixture_json"

    def collect(self, source_config: dict[str, Any]) -> list[dict[str, Any]]:
        fixture_path = source_config.get("fixture_path")
        if not fixture_path:
            raise SourceAdapterError("FIXTURE_PATH_REQUIRED")

        path = Path(fixture_path)
        if not path.exists():
            raise SourceAdapterError("FIXTURE_FILE_NOT_FOUND")

        data = json.loads(path.read_text(encoding="utf-8"))
        items = data.get("items", data) if isinstance(data, dict) else data

        if not isinstance(items, list):
            raise SourceAdapterError("FIXTURE_ITEMS_MUST_BE_LIST")

        return [dict(item) for item in items]


class AffiliateFeedSourceAdapter(BaseSourceAdapter):
    source_name = "affiliate_feed"

    def collect(self, source_config: dict[str, Any]) -> list[dict[str, Any]]:
        content = source_config.get("content")
        if content is None:
            raise SourceAdapterError("AFFILIATE_FEED_CONTENT_REQUIRED")

        data = json.loads(content)
        items = data.get("products", data) if isinstance(data, dict) else data

        if not isinstance(items, list):
            raise SourceAdapterError("AFFILIATE_FEED_ITEMS_MUST_BE_LIST")

        normalized = []
        for item in items:
            normalized.append(
                {
                    "external_offer_id": str(
                        item.get("external_offer_id")
                        or item.get("id")
                        or ""
                    ),
                    "product_title": item.get("product_title")
                    or item.get("title")
                    or "",
                    "product_url": item.get("product_url")
                    or item.get("url")
                    or "",
                    "price": item.get("price"),
                    "currency": item.get("currency", "EUR"),
                    "availability": item.get(
                        "availability",
                        "unknown",
                    ),
                    "seller_name": item.get("seller_name"),
                    "observed_at": item.get("observed_at"),
                    "raw_payload": item,
                }
            )

        return normalized


class SourceAdapterFactory:
    _adapters = {
        "fixture_json": FixtureJSONSourceAdapter,
        "affiliate_feed": AffiliateFeedSourceAdapter,
    }

    @classmethod
    def create(cls, adapter_type: str) -> BaseSourceAdapter:
        adapter_class = cls._adapters.get(adapter_type.lower())
        if adapter_class is None:
            raise SourceAdapterError("UNSUPPORTED_SOURCE_ADAPTER")
        return adapter_class()
