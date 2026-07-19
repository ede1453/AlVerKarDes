from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

from app.domains.amazon_connector.service import (
    AmazonCreatorsConfig,
    AmazonCreatorsConnectorService,
)


def _http_transport(
    *,
    method: str,
    url: str,
    headers: dict[str, str],
    json: dict[str, Any],
    timeout: float,
) -> dict[str, Any]:
    body = __import__("json").dumps(
        json,
        ensure_ascii=False,
    ).encode("utf-8")

    request = urllib.request.Request(
        url=url,
        data=body,
        headers=headers,
        method=method,
    )

    try:
        with urllib.request.urlopen(
            request,
            timeout=timeout,
        ) as response:
            return {
                "status_code": response.status,
                "json": __import__("json").loads(
                    response.read().decode("utf-8")
                ),
            }
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8")

        try:
            payload = __import__("json").loads(raw)
        except ValueError:
            payload = {"message": raw}

        return {
            "status_code": exc.code,
            "json": payload,
        }


def _fixture_transport(
    fixture_path: Path,
):
    def transport(**_: Any) -> dict[str, Any]:
        return {
            "status_code": 200,
            "json": json.loads(
                fixture_path.read_text(
                    encoding="utf-8"
                )
            ),
        }

    return transport


def build_amazon_connector() -> AmazonCreatorsConnectorService:
    fixture_mode = (
        os.getenv(
            "AMAZON_CREATORS_FIXTURE_MODE",
            "false",
        ).lower()
        == "true"
    )

    config = AmazonCreatorsConfig(
        base_url=os.getenv(
            "AMAZON_CREATORS_BASE_URL",
            "https://api.amazon.example",
        ),
        marketplace=os.getenv(
            "AMAZON_CREATORS_MARKETPLACE",
            "amazon.de",
        ),
        partner_tag=os.getenv(
            "AMAZON_CREATORS_PARTNER_TAG",
            "",
        ),
        client_id=os.getenv(
            "AMAZON_CREATORS_CLIENT_ID",
            "",
        ),
        client_secret=os.getenv(
            "AMAZON_CREATORS_CLIENT_SECRET",
            "",
        ),
        timeout_seconds=float(
            os.getenv(
                "AMAZON_CREATORS_TIMEOUT_SECONDS",
                "15",
            )
        ),
        maximum_retries=int(
            os.getenv(
                "AMAZON_CREATORS_MAXIMUM_RETRIES",
                "3",
            )
        ),
        cache_ttl_seconds=int(
            os.getenv(
                "AMAZON_CREATORS_CACHE_TTL_SECONDS",
                "300",
            )
        ),
        requests_per_second=float(
            os.getenv(
                "AMAZON_CREATORS_REQUESTS_PER_SECOND",
                "1",
            )
        ),
        fixture_mode=fixture_mode,
    )

    if fixture_mode:
        fixture_path = Path(
            os.getenv(
                "AMAZON_CREATORS_FIXTURE_PATH",
                "fixtures/amazon/search_response.json",
            )
        )
        transport = _fixture_transport(
            fixture_path
        )
    else:
        transport = _http_transport

    return AmazonCreatorsConnectorService(
        config,
        http_transport=transport,
    )
