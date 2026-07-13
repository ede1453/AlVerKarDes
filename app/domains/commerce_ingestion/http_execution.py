from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from hashlib import sha256
from typing import Any
from urllib.parse import urlparse


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


def now_iso() -> str:
    return now_utc().isoformat()


@dataclass
class HttpResponse:
    status_code: int
    headers: dict[str, str]
    body: str
    elapsed_ms: float


class HttpTransport:
    def get(
        self,
        url: str,
        *,
        headers: dict[str, str] | None = None,
        timeout_seconds: int = 15,
    ) -> HttpResponse:
        raise NotImplementedError


class FixtureHttpTransport(HttpTransport):
    def __init__(
        self,
        responses: dict[str, HttpResponse] | None = None,
    ) -> None:
        self.responses = responses or {}
        self.calls: list[dict[str, Any]] = []

    def get(
        self,
        url: str,
        *,
        headers: dict[str, str] | None = None,
        timeout_seconds: int = 15,
    ) -> HttpResponse:
        self.calls.append(
            {
                "url": url,
                "headers": headers or {},
                "timeout_seconds": timeout_seconds,
            }
        )

        response = self.responses.get(url)
        if response is None:
            return HttpResponse(
                status_code=404,
                headers={},
                body="",
                elapsed_ms=1.0,
            )

        return response


class RobotsPolicyService:
    def __init__(self) -> None:
        self._rules: dict[str, dict[str, Any]] = {}

    def set_policy(
        self,
        *,
        domain: str,
        allowed_paths: list[str] | None = None,
        disallowed_paths: list[str] | None = None,
        crawl_delay_seconds: int = 0,
    ) -> dict[str, Any]:
        policy = {
            "domain": domain.lower(),
            "allowed_paths": allowed_paths or ["/"],
            "disallowed_paths": disallowed_paths or [],
            "crawl_delay_seconds": max(
                int(crawl_delay_seconds),
                0,
            ),
        }
        self._rules[domain.lower()] = policy
        return {
            "updated": True,
            "policy": dict(policy),
        }

    def evaluate(self, url: str) -> dict[str, Any]:
        parsed = urlparse(url)
        domain = parsed.netloc.lower()
        path = parsed.path or "/"

        policy = self._rules.get(domain)

        if policy is None:
            return {
                "allowed": False,
                "reason": "ROBOTS_POLICY_UNKNOWN",
                "crawl_delay_seconds": 0,
            }

        for disallowed in policy["disallowed_paths"]:
            if path.startswith(disallowed):
                return {
                    "allowed": False,
                    "reason": "PATH_DISALLOWED",
                    "crawl_delay_seconds": policy[
                        "crawl_delay_seconds"
                    ],
                }

        allowed = any(
            path.startswith(prefix)
            for prefix in policy["allowed_paths"]
        )

        return {
            "allowed": allowed,
            "reason": (
                "PATH_ALLOWED"
                if allowed
                else "PATH_NOT_ALLOWED"
            ),
            "crawl_delay_seconds": policy[
                "crawl_delay_seconds"
            ],
        }


class DomainRateLimiter:
    def __init__(self) -> None:
        self._last_request_at: dict[str, datetime] = {}

    def check(
        self,
        *,
        domain: str,
        minimum_interval_seconds: int,
        at_time: datetime | None = None,
    ) -> dict[str, Any]:
        current = at_time or now_utc()
        previous = self._last_request_at.get(domain)

        if previous is None:
            self._last_request_at[domain] = current
            return {
                "allowed": True,
                "retry_after_seconds": 0,
            }

        elapsed = (
            current - previous
        ).total_seconds()

        if elapsed < minimum_interval_seconds:
            return {
                "allowed": False,
                "retry_after_seconds": round(
                    minimum_interval_seconds - elapsed,
                    3,
                ),
            }

        self._last_request_at[domain] = current

        return {
            "allowed": True,
            "retry_after_seconds": 0,
        }


class ResponseCache:
    def __init__(self) -> None:
        self._entries: dict[str, dict[str, Any]] = {}

    def _key(self, url: str) -> str:
        return sha256(
            url.encode("utf-8")
        ).hexdigest()

    def set(
        self,
        *,
        url: str,
        response: HttpResponse,
        ttl_seconds: int,
    ) -> dict[str, Any]:
        key = self._key(url)
        self._entries[key] = {
            "url": url,
            "response": response,
            "expires_at": (
                now_utc()
                + timedelta(seconds=ttl_seconds)
            ),
        }
        return {
            "stored": True,
            "cache_key": key,
        }

    def get(self, url: str) -> HttpResponse | None:
        key = self._key(url)
        entry = self._entries.get(key)

        if entry is None:
            return None

        if entry["expires_at"] <= now_utc():
            self._entries.pop(key, None)
            return None

        return entry["response"]


class ConnectorErrorClassifier:
    def classify(
        self,
        *,
        status_code: int | None = None,
        exception_name: str | None = None,
    ) -> dict[str, Any]:
        if exception_name in {
            "TimeoutError",
            "ConnectTimeout",
            "ReadTimeout",
        }:
            return {
                "category": "TIMEOUT",
                "retryable": True,
            }

        if status_code is None:
            return {
                "category": "UNKNOWN",
                "retryable": False,
            }

        if status_code == 429:
            return {
                "category": "RATE_LIMITED",
                "retryable": True,
            }

        if 500 <= status_code <= 599:
            return {
                "category": "UPSTREAM_SERVER_ERROR",
                "retryable": True,
            }

        if status_code in {401, 403}:
            return {
                "category": "AUTHORIZATION_ERROR",
                "retryable": False,
            }

        if status_code == 404:
            return {
                "category": "NOT_FOUND",
                "retryable": False,
            }

        if 200 <= status_code <= 299:
            return {
                "category": "SUCCESS",
                "retryable": False,
            }

        return {
            "category": "CLIENT_ERROR",
            "retryable": False,
        }


class ConnectorSlaMetrics:
    def __init__(self) -> None:
        self._metrics: dict[str, dict[str, Any]] = {}

    def record(
        self,
        *,
        connector_id: str,
        success: bool,
        duration_ms: float,
    ) -> dict[str, Any]:
        state = self._metrics.setdefault(
            connector_id,
            {
                "connector_id": connector_id,
                "request_count": 0,
                "success_count": 0,
                "failure_count": 0,
                "total_duration_ms": 0.0,
            },
        )

        state["request_count"] += 1
        state["success_count"] += int(success)
        state["failure_count"] += int(not success)
        state["total_duration_ms"] += float(duration_ms)

        return self.get(connector_id)

    def get(self, connector_id: str) -> dict[str, Any]:
        state = self._metrics.get(
            connector_id,
            {
                "connector_id": connector_id,
                "request_count": 0,
                "success_count": 0,
                "failure_count": 0,
                "total_duration_ms": 0.0,
            },
        )

        count = state["request_count"]

        return {
            "connector_id": connector_id,
            "request_count": count,
            "success_count": state["success_count"],
            "failure_count": state["failure_count"],
            "success_rate": (
                round(
                    state["success_count"] / count,
                    4,
                )
                if count
                else 0.0
            ),
            "average_duration_ms": (
                round(
                    state["total_duration_ms"] / count,
                    3,
                )
                if count
                else 0.0
            ),
            "metadata": {
                "sla_version": "connector_sla_v1"
            },
        }


class HttpConnectorExecutionService:
    def __init__(
        self,
        transport: HttpTransport,
    ) -> None:
        self.transport = transport
        self.robots = RobotsPolicyService()
        self.rate_limiter = DomainRateLimiter()
        self.cache = ResponseCache()
        self.classifier = ConnectorErrorClassifier()
        self.sla = ConnectorSlaMetrics()

    def execute(
        self,
        *,
        connector_id: str,
        url: str,
        headers: dict[str, str] | None = None,
        timeout_seconds: int = 15,
        cache_ttl_seconds: int = 0,
    ) -> dict[str, Any]:
        policy = self.robots.evaluate(url)

        if not policy["allowed"]:
            return {
                "executed": False,
                "reason": policy["reason"],
                "response": None,
            }

        parsed = urlparse(url)
        minimum_interval = policy[
            "crawl_delay_seconds"
        ]

        rate = self.rate_limiter.check(
            domain=parsed.netloc.lower(),
            minimum_interval_seconds=minimum_interval,
        )

        if not rate["allowed"]:
            return {
                "executed": False,
                "reason": "DOMAIN_RATE_LIMITED",
                "retry_after_seconds": rate[
                    "retry_after_seconds"
                ],
                "response": None,
            }

        if cache_ttl_seconds > 0:
            cached = self.cache.get(url)
            if cached is not None:
                return {
                    "executed": True,
                    "reason": "CACHE_HIT",
                    "cached": True,
                    "response": {
                        "status_code": cached.status_code,
                        "headers": cached.headers,
                        "body": cached.body,
                        "elapsed_ms": cached.elapsed_ms,
                    },
                }

        response = self.transport.get(
            url,
            headers=headers,
            timeout_seconds=timeout_seconds,
        )

        classification = self.classifier.classify(
            status_code=response.status_code
        )

        success = 200 <= response.status_code <= 299

        self.sla.record(
            connector_id=connector_id,
            success=success,
            duration_ms=response.elapsed_ms,
        )

        if success and cache_ttl_seconds > 0:
            self.cache.set(
                url=url,
                response=response,
                ttl_seconds=cache_ttl_seconds,
            )

        return {
            "executed": True,
            "reason": "HTTP_REQUEST_COMPLETED",
            "cached": False,
            "classification": classification,
            "response": {
                "status_code": response.status_code,
                "headers": response.headers,
                "body": response.body,
                "elapsed_ms": response.elapsed_ms,
            },
        }
