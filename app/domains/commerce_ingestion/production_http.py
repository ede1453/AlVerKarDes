from __future__ import annotations

import json
from dataclasses import dataclass
from time import perf_counter
from typing import Any
from urllib import error, request


@dataclass
class TransportResponse:
    status_code: int
    headers: dict[str, str]
    body: str
    elapsed_ms: float


class ProductionHttpTransport:
    def get(
        self,
        url: str,
        *,
        headers: dict[str, str] | None = None,
        timeout_seconds: int = 15,
    ) -> TransportResponse:
        started = perf_counter()
        req = request.Request(
            url=url,
            headers=headers or {},
            method="GET",
        )

        try:
            with request.urlopen(
                req,
                timeout=timeout_seconds,
            ) as response:
                body = response.read().decode(
                    "utf-8",
                    errors="replace",
                )
                elapsed_ms = (
                    perf_counter() - started
                ) * 1000

                return TransportResponse(
                    status_code=response.status,
                    headers={
                        key.lower(): value
                        for key, value in response.headers.items()
                    },
                    body=body,
                    elapsed_ms=elapsed_ms,
                )
        except error.HTTPError as exc:
            body = exc.read().decode(
                "utf-8",
                errors="replace",
            )
            elapsed_ms = (
                perf_counter() - started
            ) * 1000

            return TransportResponse(
                status_code=exc.code,
                headers={
                    key.lower(): value
                    for key, value in exc.headers.items()
                },
                body=body,
                elapsed_ms=elapsed_ms,
            )


class ConditionalRequestState:
    def __init__(self) -> None:
        self._state: dict[str, dict[str, str]] = {}

    def build_headers(
        self,
        url: str,
    ) -> dict[str, str]:
        state = self._state.get(url, {})
        headers: dict[str, str] = {}

        if state.get("etag"):
            headers["If-None-Match"] = state["etag"]

        if state.get("last_modified"):
            headers["If-Modified-Since"] = state[
                "last_modified"
            ]

        return headers

    def update(
        self,
        *,
        url: str,
        headers: dict[str, str],
    ) -> dict[str, str]:
        normalized = {
            key.lower(): value
            for key, value in headers.items()
        }

        state = {
            "etag": normalized.get("etag", ""),
            "last_modified": normalized.get(
                "last-modified",
                "",
            ),
        }

        self._state[url] = state
        return dict(state)


class ResponseContentValidator:
    ALLOWED_CONTENT_TYPES = {
        "application/json",
        "application/ld+json",
        "text/json",
    }

    def validate(
        self,
        *,
        status_code: int,
        headers: dict[str, str],
        body: str,
        max_body_bytes: int = 2_000_000,
    ) -> dict[str, Any]:
        if status_code == 304:
            return {
                "valid": True,
                "reason": "NOT_MODIFIED",
                "parsed": None,
            }

        if not 200 <= status_code <= 299:
            return {
                "valid": False,
                "reason": "NON_SUCCESS_STATUS",
                "parsed": None,
            }

        body_size = len(
            body.encode("utf-8")
        )

        if body_size > max_body_bytes:
            return {
                "valid": False,
                "reason": "BODY_TOO_LARGE",
                "parsed": None,
            }

        content_type = (
            headers.get("content-type", "")
            .split(";")[0]
            .strip()
            .lower()
        )

        if content_type not in self.ALLOWED_CONTENT_TYPES:
            return {
                "valid": False,
                "reason": "UNSUPPORTED_CONTENT_TYPE",
                "parsed": None,
            }

        try:
            parsed = json.loads(body)
        except json.JSONDecodeError:
            return {
                "valid": False,
                "reason": "INVALID_JSON",
                "parsed": None,
            }

        return {
            "valid": True,
            "reason": "CONTENT_VALID",
            "parsed": parsed,
        }


class PaginationService:
    def get_next_url(
        self,
        *,
        payload: Any,
        headers: dict[str, str],
    ) -> str | None:
        if isinstance(payload, dict):
            next_url = (
                payload.get("next")
                or payload.get("next_url")
            )

            if isinstance(
                payload.get("pagination"),
                dict,
            ):
                next_url = (
                    next_url
                    or payload["pagination"].get(
                        "next"
                    )
                )

            if next_url:
                return str(next_url)

        link_header = headers.get(
            "link",
            "",
        )

        for segment in link_header.split(","):
            if 'rel="next"' not in segment:
                continue

            start = segment.find("<")
            end = segment.find(">")

            if start >= 0 and end > start:
                return segment[
                    start + 1:end
                ].strip()

        return None


class MultiPageConnectorRuntime:
    def __init__(
        self,
        transport: Any,
    ) -> None:
        self.transport = transport
        self.conditional = ConditionalRequestState()
        self.validator = ResponseContentValidator()
        self.pagination = PaginationService()

    def execute(
        self,
        *,
        start_url: str,
        base_headers: dict[str, str] | None = None,
        timeout_seconds: int = 15,
        max_pages: int = 10,
    ) -> dict[str, Any]:
        current_url: str | None = start_url
        page_count = 0
        collected_items: list[dict[str, Any]] = []
        visited_urls: list[str] = []
        stopped_reason = "NO_MORE_PAGES"

        while current_url and page_count < max_pages:
            if current_url in visited_urls:
                stopped_reason = "PAGINATION_LOOP_DETECTED"
                break

            visited_urls.append(current_url)

            headers = dict(base_headers or {})
            headers.update(
                self.conditional.build_headers(
                    current_url
                )
            )

            response = self.transport.get(
                current_url,
                headers=headers,
                timeout_seconds=timeout_seconds,
            )

            validation = self.validator.validate(
                status_code=response.status_code,
                headers={
                    key.lower(): value
                    for key, value in response.headers.items()
                },
                body=response.body,
            )

            page_count += 1

            if response.status_code == 304:
                stopped_reason = "NOT_MODIFIED"
                break

            if not validation["valid"]:
                return {
                    "executed": False,
                    "reason": validation["reason"],
                    "page_count": page_count,
                    "items": collected_items,
                    "visited_urls": visited_urls,
                }

            self.conditional.update(
                url=current_url,
                headers=response.headers,
            )

            payload = validation["parsed"]

            if isinstance(payload, dict):
                items = (
                    payload.get("items")
                    or payload.get("products")
                    or []
                )
            elif isinstance(payload, list):
                items = payload
            else:
                items = []

            if not isinstance(items, list):
                return {
                    "executed": False,
                    "reason": "ITEMS_NOT_LIST",
                    "page_count": page_count,
                    "items": collected_items,
                    "visited_urls": visited_urls,
                }

            collected_items.extend(
                dict(item)
                for item in items
            )

            current_url = self.pagination.get_next_url(
                payload=payload,
                headers={
                    key.lower(): value
                    for key, value in response.headers.items()
                },
            )

        if current_url and page_count >= max_pages:
            stopped_reason = "MAX_PAGES_REACHED"

        return {
            "executed": True,
            "reason": stopped_reason,
            "page_count": page_count,
            "item_count": len(collected_items),
            "items": collected_items,
            "visited_urls": visited_urls,
            "metadata": {
                "runtime_version": "production_http_runtime_v1"
            },
        }
