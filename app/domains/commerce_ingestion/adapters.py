from __future__ import annotations

import csv
import json
from io import StringIO
from typing import Any


class BaseFeedAdapter:
    adapter_type = "base"

    def parse(self, content: str) -> list[dict[str, Any]]:
        raise NotImplementedError


class CSVFeedAdapter(BaseFeedAdapter):
    adapter_type = "csv"

    def parse(self, content: str) -> list[dict[str, Any]]:
        reader = csv.DictReader(StringIO(content))
        return [dict(row) for row in reader]


class JSONFeedAdapter(BaseFeedAdapter):
    adapter_type = "json"

    def parse(self, content: str) -> list[dict[str, Any]]:
        data = json.loads(content)
        if isinstance(data, dict):
            items = data.get("items", [])
        else:
            items = data
        if not isinstance(items, list):
            raise ValueError("JSON feed must contain a list of items")
        return [dict(item) for item in items]


class ManualFeedAdapter(BaseFeedAdapter):
    adapter_type = "manual"

    def parse(self, content: str) -> list[dict[str, Any]]:
        data = json.loads(content)
        if not isinstance(data, list):
            raise ValueError("Manual feed must be a JSON list")
        return [dict(item) for item in data]


class AdapterFactory:
    _adapters = {
        "csv": CSVFeedAdapter,
        "json": JSONFeedAdapter,
        "manual": ManualFeedAdapter,
    }

    @classmethod
    def create(cls, adapter_type: str) -> BaseFeedAdapter:
        adapter_class = cls._adapters.get(adapter_type.lower())
        if adapter_class is None:
            raise ValueError("UNSUPPORTED_ADAPTER_TYPE")
        return adapter_class()
