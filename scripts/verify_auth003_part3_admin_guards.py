"""AUTH-003 Part 3 verification script.

Sends real, unauthenticated HTTP requests (no Authorization header) to every
one of the 188 endpoints classified ADMIN_ONLY in AUTH-003 Part 3, against a
REAL running server (not TestClient/ASGI transport) at http://localhost:8000,
per this project's "gercek istekle dogrula" (verify with a real request)
discipline already used for AUTH-003 Parts 1 and 2.

This is a REPORTING tool only. It does not assert or fail the process on a
non-401 result -- some of the 188 endpoints require a non-optional JSON body,
and FastAPI validates path/query params and the request body BEFORE most
Depends() dependencies run in some cases, so a bare/empty-body POST can trip
a 422 before get_current_user() ever executes. That is a real thing worth a
human's attention, not something this script should silently swallow or try
to route around by guessing 188 different valid payloads. It is printed as a
flagged "non-401" result for a human (not this script) to interpret.

Usage:
    python scripts/verify_auth003_part3_admin_guards.py
    python scripts/verify_auth003_part3_admin_guards.py --base-url http://localhost:8000
    python scripts/verify_auth003_part3_admin_guards.py --timeout 10
"""

from __future__ import annotations

import argparse
import re
import sys
import uuid
from dataclasses import dataclass

try:
    import httpx as _http_lib

    _USING = "httpx"
except ImportError:  # pragma: no cover - fallback if httpx isn't installed
    try:
        import requests as _http_lib  # type: ignore[no-redef]

        _USING = "requests"
    except ImportError:
        print(
            "Neither httpx nor requests is installed. Install one of them, e.g.:\n"
            "    pip install httpx\n",
            file=sys.stderr,
        )
        sys.exit(2)


# ---------------------------------------------------------------------------
# The 188 ADMIN_ONLY endpoints (AUTH-003 Part 3), embedded directly so this
# script has no dependency on the scratch-directory list file it was
# generated from. (method, path) pairs, exactly as classified.
# Two rows are additionally flagged upstream as "belirsiz, gozden gecirilmeli"
# (uncertain, needs review) -- see UNCERTAIN_PATHS below; they are still
# tested like every other endpoint here, the flag is informational only.
# ---------------------------------------------------------------------------

ENDPOINTS: list[tuple[str, str]] = [
    ("GET", "/api/v1/llm-audit-traces"),
    ("POST", "/api/v1/llm-audit-traces"),
    ("POST", "/api/v1/llm-audit-traces/db"),
    ("GET", "/api/v1/llm-audit-traces/db/list"),
    ("GET", "/api/v1/llm-audit-traces/db/{trace_id}"),
    ("GET", "/api/v1/llm-audit-traces/{trace_id}"),
    ("POST", "/api/v1/llm-explanations/prepare"),
    ("POST", "/api/v1/llm-orchestration/run"),
    ("POST", "/api/v1/llm-orchestration/run-guarded"),
    ("POST", "/api/v1/llm-orchestration/run-guarded-with-audit"),
    ("POST", "/api/v1/llm-orchestration/run-intelligent"),
    ("POST", "/api/v1/llm-orchestration/run-with-audit"),
    ("POST", "/api/v1/llm-orchestration/run-with-db-audit"),
    ("POST", "/api/v1/llm-gateway/generate"),
    ("GET", "/api/v1/llm-gateway/providers"),
    ("POST", "/api/v1/llm-provider-health/check"),
    ("GET", "/api/v1/llm-provider-health/summary"),
    ("POST", "/api/v1/llm-provider-selection/select"),
    ("POST", "/api/v1/llm-streaming/preview"),
    ("POST", "/api/v1/llm-streaming/sse"),
    ("GET", "/api/v1/amazon-connector/metrics"),
    ("POST", "/api/v1/connector-operations/clear"),
    ("POST", "/api/v1/connector-operations/credential-profiles"),
    ("GET", "/api/v1/connector-operations/credential-profiles/{profile_id}"),
    ("POST", "/api/v1/connector-operations/metrics"),
    ("GET", "/api/v1/connector-operations/metrics/{source_id}"),
    ("GET", "/api/v1/connector-operations/readiness"),
    ("POST", "/api/v1/connector-operations/retry"),
    ("POST", "/api/v1/connector-operations/retry/{operation_key}/reset"),
    ("POST", "/api/v1/connector-operations/schedules"),
    ("GET", "/api/v1/connector-operations/schedules/due"),
    ("POST", "/api/v1/connector-operations/schedules/{schedule_id}/mark-run"),
    ("POST", "/api/v1/connector-operations/validate-items"),
    ("POST", "/api/v1/admin/import/upload"),
    ("POST", "/api/v1/market/connectors/import"),
    ("POST", "/api/v1/deal-notification-operations/clear"),
    ("POST", "/api/v1/deal-notification-operations/delivery-attempts"),
    ("GET", "/api/v1/deal-notification-operations/delivery-attempts/{notification_id}"),
    ("POST", "/api/v1/deal-notification-operations/digests"),
    ("POST", "/api/v1/deal-notification-operations/engagement"),
    ("GET", "/api/v1/deal-notification-operations/engagement/metrics"),
    ("POST", "/api/v1/deal-notification-operations/escalations"),
    ("POST", "/api/v1/deal-notification-operations/escalations/{escalation_id}/complete"),
    ("POST", "/api/v1/deal-notification-operations/idempotency/reserve"),
    ("POST", "/api/v1/deal-notification-providers/clear"),
    ("POST", "/api/v1/deal-notification-providers/delivery-policy/evaluate"),
    ("POST", "/api/v1/deal-notification-providers/experiments"),
    ("GET", "/api/v1/deal-notification-providers/experiments/{experiment_id}/assign"),
    ("POST", "/api/v1/deal-notification-providers/performance"),
    ("POST", "/api/v1/deal-notification-providers/providers"),
    ("GET", "/api/v1/deal-notification-providers/providers/select"),
    ("POST", "/api/v1/deal-notification-providers/subscriptions"),
    ("GET", "/api/v1/deal-notification-providers/subscriptions/unsubscribed"),
    ("POST", "/api/v1/deal-operations/clear"),
    ("POST", "/api/v1/deal-operations/evaluate"),
    ("GET", "/api/v1/deal-operations/opportunities/{opportunity_id}"),
    ("GET", "/api/v1/deal-operations/opportunities/{opportunity_id}/decisions"),
    ("GET", "/api/v1/deal-operations/watchlist"),
    ("POST", "/api/v1/deal-operations/watchlist"),
    ("POST", "/api/v1/deal-storage-operations/backup-schedules"),
    ("POST", "/api/v1/deal-storage-operations/backup-schedules/{schedule_id}/run"),
    ("POST", "/api/v1/deal-storage-operations/clear"),
    ("POST", "/api/v1/deal-storage-operations/health-dashboard"),
    ("POST", "/api/v1/deal-storage-operations/notification-bridge"),
    ("GET", "/api/v1/deal-storage-operations/notifications"),
    ("POST", "/api/v1/deal-storage-operations/restore-drills"),
    ("POST", "/api/v1/deal-storage-operations/worker/run"),
    ("GET", "/api/v1/deal-storage-operations/worker/runs"),
    ("POST", "/api/v1/deal-storage-resilience/backup-exports"),
    ("GET", "/api/v1/deal-storage-resilience/backup-exports/{export_id}"),
    ("POST", "/api/v1/deal-storage-resilience/backup-exports/{export_id}/validate"),
    ("POST", "/api/v1/deal-storage-resilience/clear"),
    ("POST", "/api/v1/deal-storage-resilience/dead-letters/{dead_letter_id}/replay"),
    ("POST", "/api/v1/deal-storage-resilience/health"),
    ("GET", "/api/v1/deal-storage-resilience/health/latest"),
    ("POST", "/api/v1/deal-storage-resilience/outbox"),
    ("POST", "/api/v1/deal-storage-resilience/outbox/claim"),
    ("POST", "/api/v1/deal-storage-resilience/outbox/{event_id}/failed"),
    ("POST", "/api/v1/deal-storage-resilience/outbox/{event_id}/published"),
    ("POST", "/api/v1/rate-limits/check"),
    ("POST", "/api/v1/product-canonicalization/canonicalize"),
    ("POST", "/api/v1/product-canonicalization/canonicalize-cached"),
    ("POST", "/api/v1/product-matching/match"),
    ("POST", "/api/v1/product-matching/match-cached"),
    ("POST", "/api/v1/products/intelligence/merge-candidates"),
    ("POST", "/api/v1/products/intelligence/merge-candidates/persist"),
    ("POST", "/api/v1/products/intelligence/merge-candidates/{candidate_id}/apply"),
    ("PATCH", "/api/v1/products/intelligence/merge-candidates/{candidate_id}/review"),
    ("POST", "/api/v1/products/merge/apply"),
    ("POST", "/api/v1/products/cleanup/orphans"),
    ("POST", "/api/v1/products/merge/verify"),
    ("POST", "/api/v1/products/"),
    ("POST", "/api/v1/products/brands"),
    ("POST", "/api/v1/products/categories"),
    ("POST", "/api/v1/products/from-name"),
    ("POST", "/api/v1/notification-outbox/batch-summary"),
    ("GET", "/api/v1/notification-outbox/channel-health"),
    ("GET", "/api/v1/notification-outbox/circuit-breaker/status"),
    ("POST", "/api/v1/notification-outbox/clear"),
    ("GET", "/api/v1/notification-outbox/dead-letters"),
    ("POST", "/api/v1/notification-outbox/dead-letters/{item_id}/replay"),
    ("GET", "/api/v1/notification-outbox/leader/status"),
    ("GET", "/api/v1/notification-outbox/metrics"),
    ("GET", "/api/v1/notification-outbox/pending"),
    ("GET", "/api/v1/notification-outbox/priority-queue/{priority}"),
    ("POST", "/api/v1/notification-outbox/readiness/checks"),
    ("GET", "/api/v1/notification-outbox/readiness/status"),
    ("POST", "/api/v1/notification-outbox/release-approval/approve"),
    ("POST", "/api/v1/notification-outbox/release-approval/revoke"),
    ("GET", "/api/v1/notification-outbox/release-approval/status"),
    ("GET", "/api/v1/notification-outbox/release-audit/events"),
    ("POST", "/api/v1/notification-outbox/release-audit/events"),
    ("GET", "/api/v1/notification-outbox/release-manifest"),
    ("POST", "/api/v1/notification-outbox/release-manifest/publish"),
    ("POST", "/api/v1/notification-outbox/release-promotion/promote"),
    ("GET", "/api/v1/notification-outbox/release-promotion/status"),
    ("POST", "/api/v1/notification-outbox/release-rollback/complete"),
    ("POST", "/api/v1/notification-outbox/release-rollback/request"),
    ("GET", "/api/v1/notification-outbox/release-rollback/status"),
    ("GET", "/api/v1/notification-outbox/scaling/instances/status"),
    ("POST", "/api/v1/notification-outbox/scheduler/jobs"),
    ("POST", "/api/v1/notification-outbox/scheduler/jobs/{job_name}/run"),
    ("GET", "/api/v1/notification-outbox/scheduler/status"),
    ("POST", "/api/v1/notification-outbox/template-preview"),
    ("GET", "/api/v1/notification-outbox/tenant-quota/{tenant_id}"),
    ("GET", "/api/v1/notification-outbox/workers/status"),
    ("POST", "/api/v1/cache/clear"),
    ("POST", "/api/v1/cache/get"),
    ("POST", "/api/v1/cache/key"),
    ("POST", "/api/v1/cache/set"),
    ("GET", "/api/v1/cache/status"),
    ("GET", "/api/v1/observability/audit-events"),
    ("POST", "/api/v1/observability/audit-events"),
    ("POST", "/api/v1/observability/clear"),
    ("GET", "/api/v1/observability/logs"),
    ("POST", "/api/v1/observability/logs"),
    ("GET", "/api/v1/observability/snapshot"),
    ("POST", "/api/v1/observability/snapshot"),
    ("GET", "/api/v1/observability/timelines/{correlation_id}"),
    ("GET", "/api/v1/observability/traces/{trace_id}"),
    ("POST", "/api/v1/production-http/clear"),
    ("POST", "/api/v1/production-http/execute"),
    ("POST", "/api/v1/production-http/fixture-pages"),
    ("POST", "/api/v1/production-launch/clear"),
    ("POST", "/api/v1/production-launch/{operation}"),
    ("GET", "/api/v1/runtime-settings/status"),
    ("GET", "/api/v1/storage-production-readiness/access-events"),
    ("POST", "/api/v1/storage-production-readiness/access-events"),
    ("POST", "/api/v1/storage-production-readiness/capacity"),
    ("POST", "/api/v1/storage-production-readiness/clear"),
    ("POST", "/api/v1/storage-production-readiness/encryption-compliance"),
    ("POST", "/api/v1/storage-production-readiness/encryption-policies"),
    ("POST", "/api/v1/storage-production-readiness/maintenance-windows"),
    ("POST", "/api/v1/storage-production-readiness/maintenance-windows/evaluate"),
    ("POST", "/api/v1/storage-production-readiness/readiness"),
    ("GET", "/api/v1/storage-production-readiness/readiness/latest"),
    ("POST", "/api/v1/storage-reliability/backups"),
    ("POST", "/api/v1/storage-reliability/backups/retention-evaluate"),
    ("POST", "/api/v1/storage-reliability/clear"),
    ("POST", "/api/v1/storage-reliability/dr-plans"),
    ("POST", "/api/v1/storage-reliability/dr-plans/{plan_id}/tests"),
    ("POST", "/api/v1/storage-reliability/restore-approvals"),
    ("GET", "/api/v1/storage-reliability/restore-approvals/{approval_id}/can-execute"),
    ("POST", "/api/v1/storage-reliability/restore-approvals/{approval_id}/decision"),
    ("POST", "/api/v1/storage-reliability/slo-samples"),
    ("GET", "/api/v1/storage-reliability/slo-samples/latest"),
    ("POST", "/api/v1/storage-reliability/worker-leases"),
    ("POST", "/api/v1/storage-reliability/worker-leases/{worker_id}/heartbeat"),
    ("POST", "/api/v1/storage-reliability/worker-leases/{worker_id}/release"),
    ("GET", "/api/v1/integrity/duplicate-product-regression"),
    ("GET", "/api/v1/integrity/check"),
    ("POST", "/api/v1/consumer-intelligence/evaluate"),
    ("POST", "/api/v1/consumer-trust/acceptance-metrics"),
    ("POST", "/api/v1/consumer-trust/budget-policy"),
    ("POST", "/api/v1/consumer-trust/category-quota"),
    ("POST", "/api/v1/consumer-trust/clear"),
    ("POST", "/api/v1/consumer-trust/delivery-sla"),
    ("POST", "/api/v1/consumer-trust/fatigue"),
    ("POST", "/api/v1/consumer-trust/feedback-summary"),
    ("POST", "/api/v1/consumer-trust/provider-fallback"),
    ("POST", "/api/v1/consumer-trust/provider-health"),
    ("POST", "/api/v1/consumer-trust/recommendation-audit"),
    ("POST", "/api/v1/consumer-trust/source-trust"),
    ("POST", "/api/v1/consumer-trust/sponsored-compliance"),
    ("POST", "/api/v1/consumer-trust/trust-dashboard"),
    ("POST", "/api/v1/growth-intelligence/clear"),
    ("POST", "/api/v1/growth-intelligence/{operation}"),
    ("POST", "/api/v1/user-value/clear"),
]

# Rows the classification doc itself flagged as "belirsiz, gozden gecirilmeli"
# (uncertain, needs review) -- informational only, still tested like the rest.
UNCERTAIN_PATHS = {
    "/api/v1/production-http/clear",
    "/api/v1/production-http/execute",
    "/api/v1/production-http/fixture-pages",
    "/api/v1/consumer-intelligence/evaluate",
}

assert len(ENDPOINTS) == 188, f"expected 188 endpoints, embedded {len(ENDPOINTS)}"


_PATH_PARAM_RE = re.compile(r"\{([^{}]+)\}")


def _placeholder_for(param_name: str) -> str:
    """Pick a syntactically-plausible placeholder for a path param so the
    route is at least reachable/routable. UUID-ish names get a random UUID;
    everything else (job names, operation slugs, tenant/priority strings,
    integer-looking ids) gets a simple, harmless string."""
    lowered = param_name.lower()
    if "id" in lowered or "uuid" in lowered:
        return str(uuid.uuid4())
    return "1"


def _fill_path(path: str) -> str:
    def _sub(match: "re.Match[str]") -> str:
        return _placeholder_for(match.group(1))

    return _PATH_PARAM_RE.sub(_sub, path)


@dataclass
class Result:
    method: str
    raw_path: str
    filled_path: str
    status_code: int | None
    error: str | None
    uncertain_flag: bool


def run(base_url: str, timeout: float) -> list[Result]:
    results: list[Result] = []

    client_kwargs = {"timeout": timeout}
    if _USING == "httpx":
        client = _http_lib.Client(base_url=base_url, **client_kwargs)
    else:  # requests has no persistent base_url client; emulate one
        client = _http_lib.Session()

    try:
        for method, raw_path in ENDPOINTS:
            filled_path = _fill_path(raw_path)
            url = filled_path if _USING == "httpx" else base_url.rstrip("/") + filled_path

            # Deliberately NO Authorization header. POST/PATCH endpoints get
            # an empty JSON object body ("{}") -- trivially satisfiable for
            # schemas where every field is optional/defaulted, and a
            # legitimate 422-before-401 signal for schemas that require a
            # field the endpoint doesn't declare a default for. We do not
            # try to guess real payloads for the 188 different schemas here
            # (see module docstring).
            kwargs: dict = {}
            if method in ("POST", "PATCH", "PUT"):
                kwargs["json"] = {}

            try:
                response = client.request(method, url, **kwargs)
                status_code: int | None = response.status_code
                error = None
            except Exception as exc:  # noqa: BLE001 - report, don't crash the sweep
                status_code = None
                error = f"{type(exc).__name__}: {exc}"

            results.append(
                Result(
                    method=method,
                    raw_path=raw_path,
                    filled_path=filled_path,
                    status_code=status_code,
                    error=error,
                    uncertain_flag=raw_path in UNCERTAIN_PATHS,
                )
            )
    finally:
        client.close()

    return results


def summarize(results: list[Result]) -> None:
    total = len(results)
    got_401 = [r for r in results if r.status_code == 401]
    not_401 = [r for r in results if r.status_code != 401]
    errored = [r for r in results if r.status_code is None]

    print("=" * 78)
    print("AUTH-003 Part 3 -- ADMIN_ONLY endpoint guard verification")
    print("=" * 78)
    print(f"Total endpoints checked : {total}")
    print(f"Returned 401 (expected) : {len(got_401)}")
    print(f"Did NOT return 401      : {len(not_401) - len(errored)}")
    print(f"Request errors          : {len(errored)}")
    print()

    if not_401:
        print("-" * 78)
        print("Non-401 results (inspect each -- may be a real gap, or a route that")
        print("legitimately 404/422s on a placeholder path/empty body before the")
        print("auth Depends() ever runs; a POST requiring a non-optional field will")
        print("commonly 422 here since this script only ever sends {} as the body):")
        print("-" * 78)
        for r in not_401:
            flag = "  [FLAGGED IN CLASSIFICATION DOC AS UNCERTAIN]" if r.uncertain_flag else ""
            if r.error is not None:
                print(f"  {r.method:6s} {r.raw_path:80s} ERROR: {r.error}{flag}")
            else:
                print(f"  {r.method:6s} {r.raw_path:80s} -> {r.status_code}{flag}")
    else:
        print("All 188 endpoints returned 401 with no Authorization header.")

    print()
    print("Reminder: this script only reports. It does not assert/fail on a")
    print("non-401 result -- review the list above yourself.")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--base-url",
        default="http://localhost:8000",
        help="Base URL of the running server (default: http://localhost:8000)",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=10.0,
        help="Per-request timeout in seconds (default: 10)",
    )
    args = parser.parse_args()

    print(f"Using HTTP client: {_USING}")
    print(f"Target server     : {args.base_url}")
    print(f"Endpoints to check: {len(ENDPOINTS)}")
    print()

    results = run(args.base_url, args.timeout)
    summarize(results)


if __name__ == "__main__":
    main()
