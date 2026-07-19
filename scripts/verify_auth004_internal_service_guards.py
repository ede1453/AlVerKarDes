"""AUTH-004 verification script.

Sends real HTTP requests (no TestClient/ASGI transport) to every one of the
93 endpoints classified INTERNAL_SERVICE, against a REAL running server
(default http://localhost:8000), per this project's "gercek istekle dogrula"
(verify with a real request) discipline already used for AUTH-003 Part 3
(see verify_auth003_part3_admin_guards.py, same shape).

Two full sweeps are run:
  1. No X-Internal-Service-Key header at all       -> every endpoint must 401.
  2. Correct X-Internal-Service-Key header supplied -> every endpoint must NOT
     401 (normal behavior -- 2xx, 404, or 422 are all "the guard let the
     request through", since this script sends {} bodies and placeholder path
     params rather than real payloads for all 93 different schemas).

This is a REPORTING tool for sweep 2 in the same sense
verify_auth003_part3_admin_guards.py is: a non-2xx result in sweep 2 is not
necessarily a bug (an empty body/placeholder id can legitimately 404/422
downstream of the guard). Sweep 1 IS asserted -- every single endpoint
returning exactly 401 with no key is the entire point of AUTH-004, so this
script exits non-zero if even one of the 93 fails to 401 without a key.

Usage:
    python scripts/verify_auth004_internal_service_guards.py --key <secret>
    python scripts/verify_auth004_internal_service_guards.py --key <secret> --base-url http://localhost:8000
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
# The 93 INTERNAL_SERVICE endpoints (AUTH-004), embedded directly (same
# pattern as AUTH-003 Part 3's script) so this has no dependency on the
# scratch-directory classification table it was derived from. Cross-checked
# programmatically against FastAPI's actual dependant graph
# (require_internal_service_key wired to exactly these 93, nothing else)
# before this script was written.
# ---------------------------------------------------------------------------

ENDPOINTS: list[tuple[str, str]] = [
    ("POST", "/api/v1/amazon-connector/collect"),
    ("POST", "/api/v1/connector-runtime/clear"),
    ("GET", "/api/v1/connector-runtime/events"),
    ("POST", "/api/v1/connector-runtime/execute"),
    ("GET", "/api/v1/connector-runtime/price-history/{canonical_product_key}"),
    ("GET", "/api/v1/connector-runtime/runs/{run_id}"),
    ("POST", "/api/v1/crawler/crawl"),
    ("POST", "/api/v1/http-connectors/clear"),
    ("POST", "/api/v1/http-connectors/execute"),
    ("POST", "/api/v1/http-connectors/fixture-responses"),
    ("POST", "/api/v1/http-connectors/robots-policy"),
    ("GET", "/api/v1/http-connectors/sla/{connector_id}"),
    ("GET", "/api/v1/provider-schedules"),
    ("POST", "/api/v1/provider-schedules"),
    ("POST", "/api/v1/provider-schedules/clear"),
    ("GET", "/api/v1/provider-schedules/{schedule_id}"),
    ("POST", "/api/v1/provider-schedules/{schedule_id}/run-once"),
    ("POST", "/api/v1/external-connectors/ingest"),
    ("POST", "/api/v1/connectors/ingest"),
    ("GET", "/api/v1/deal-persistence/archives"),
    ("POST", "/api/v1/deal-persistence/clear"),
    ("POST", "/api/v1/deal-persistence/records"),
    ("GET", "/api/v1/deal-persistence/records/{deal_id}"),
    ("POST", "/api/v1/deal-persistence/records/{deal_id}/archive"),
    ("POST", "/api/v1/deal-persistence/records/{deal_id}/checkpoints"),
    ("GET", "/api/v1/deal-persistence/records/{deal_id}/checkpoints/latest"),
    ("POST", "/api/v1/deal-persistence/records/{deal_id}/snapshots"),
    ("GET", "/api/v1/deal-persistence/recovery-events"),
    ("GET", "/api/v1/deal-persistence/snapshots/{snapshot_id}"),
    ("POST", "/api/v1/deal-persistence/snapshots/{snapshot_id}/recover"),
    ("POST", "/api/v1/deal-storage/backups"),
    ("POST", "/api/v1/deal-storage/backups/{manifest_id}/verify"),
    ("POST", "/api/v1/deal-storage/clear"),
    ("POST", "/api/v1/deal-storage/integrity/audit"),
    ("GET", "/api/v1/deal-storage/outbox"),
    ("POST", "/api/v1/deal-storage/outbox/{event_id}/publish"),
    ("POST", "/api/v1/deal-storage/records"),
    ("GET", "/api/v1/deal-storage/records/{deal_id}"),
    ("POST", "/api/v1/deal-storage/retention/purge"),
    ("POST", "/api/v1/deal-storage/transactions"),
    ("POST", "/api/v1/deal-storage-sql/backups"),
    ("POST", "/api/v1/deal-storage-sql/backups/{manifest_id}/verify"),
    ("POST", "/api/v1/deal-storage-sql/integrity/audit"),
    ("POST", "/api/v1/deal-storage-sql/outbox/claim"),
    ("POST", "/api/v1/deal-storage-sql/outbox/{event_id}/publish"),
    ("POST", "/api/v1/deal-storage-sql/records"),
    ("GET", "/api/v1/deal-storage-sql/records/{deal_id}"),
    ("POST", "/api/v1/deal-storage-sql/retention/purge"),
    ("POST", "/api/v1/deal-storage-sql/transactions"),
    ("GET", "/api/v1/events"),
    ("POST", "/api/v1/events/clear"),
    ("POST", "/api/v1/events/publish"),
    ("GET", "/api/v1/events/status"),
    ("GET", "/api/v1/jobs"),
    ("POST", "/api/v1/jobs/enqueue"),
    ("POST", "/api/v1/jobs/run-now"),
    ("GET", "/api/v1/jobs/{job_id}"),
    ("POST", "/api/v1/commerce-ingestion-execution/clear"),
    ("GET", "/api/v1/commerce-ingestion-execution/jobs"),
    ("POST", "/api/v1/commerce-ingestion-execution/jobs"),
    ("POST", "/api/v1/commerce-ingestion-execution/jobs/{job_id}/execute"),
    ("GET", "/api/v1/commerce-ingestion-execution/quarantine"),
    ("POST", "/api/v1/commerce-ingestion-execution/quarantine/{quarantine_id}/replay"),
    ("POST", "/api/v1/commerce-ingestion/clear"),
    ("POST", "/api/v1/commerce-ingestion/normalize"),
    ("POST", "/api/v1/commerce-ingestion/price-snapshots"),
    ("POST", "/api/v1/commerce-ingestion/raw-offers"),
    ("POST", "/api/v1/commerce-ingestion/runs"),
    ("POST", "/api/v1/commerce-ingestion/runs/{run_id}/complete"),
    ("GET", "/api/v1/commerce-ingestion/sources"),
    ("POST", "/api/v1/commerce-ingestion/sources"),
    ("GET", "/api/v1/commerce-ingestion/sources/{source_id}/health"),
    ("GET", "/api/v1/notification-outbox/circuit-breaker/can-deliver"),
    ("POST", "/api/v1/notification-outbox/claim-next"),
    ("POST", "/api/v1/notification-outbox/enqueue"),
    ("POST", "/api/v1/notification-outbox/enqueue-many"),
    ("POST", "/api/v1/notification-outbox/leader/acquire"),
    ("POST", "/api/v1/notification-outbox/leader/release"),
    ("POST", "/api/v1/notification-outbox/leader/renew"),
    ("POST", "/api/v1/notification-outbox/requeue-due-retries"),
    ("POST", "/api/v1/notification-outbox/scaling/assign"),
    ("POST", "/api/v1/notification-outbox/scaling/instances"),
    ("POST", "/api/v1/notification-outbox/scaling/instances/{instance_id}/release"),
    ("POST", "/api/v1/notification-outbox/workers"),
    ("POST", "/api/v1/notification-outbox/workers/assign"),
    ("POST", "/api/v1/notification-outbox/workers/{worker_id}/complete"),
    ("POST", "/api/v1/notification-outbox/{item_id}/mark-delivered"),
    ("POST", "/api/v1/notification-outbox/{item_id}/mark-failed"),
    ("POST", "/api/v1/consumer-trust/deliveries"),
    ("POST", "/api/v1/consumer-trust/frequency-cap"),
    ("POST", "/api/v1/market/offers"),
    ("POST", "/api/v1/market/prices"),
    ("POST", "/api/v1/market/stores"),
]

assert len(ENDPOINTS) == 93, f"expected 93 endpoints, embedded {len(ENDPOINTS)}"


_PATH_PARAM_RE = re.compile(r"\{([^{}]+)\}")


def _placeholder_for(param_name: str) -> str:
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


def _make_client(base_url: str, timeout: float):
    if _USING == "httpx":
        return _http_lib.Client(base_url=base_url, timeout=timeout)
    return _http_lib.Session()


def run(base_url: str, timeout: float, headers: dict[str, str]) -> list[Result]:
    results: list[Result] = []
    client = _make_client(base_url, timeout)

    try:
        for method, raw_path in ENDPOINTS:
            filled_path = _fill_path(raw_path)
            url = filled_path if _USING == "httpx" else base_url.rstrip("/") + filled_path

            kwargs: dict = {"headers": headers}
            if method in ("POST", "PATCH", "PUT"):
                kwargs["json"] = {}
            if _USING == "requests":
                kwargs["timeout"] = timeout

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
                )
            )
    finally:
        client.close()

    return results


def summarize_no_key_sweep(results: list[Result]) -> bool:
    """Returns True iff every endpoint returned exactly 401. This sweep IS
    asserted -- AUTH-004's entire point is that none of the 93 are reachable
    without the shared secret."""
    total = len(results)
    got_401 = [r for r in results if r.status_code == 401]
    not_401 = [r for r in results if r.status_code != 401]

    print("=" * 78)
    print("AUTH-004 Sweep 1/2 -- NO X-Internal-Service-Key header")
    print("=" * 78)
    print(f"Total endpoints checked : {total}")
    print(f"Returned 401 (expected) : {len(got_401)}")
    print(f"Did NOT return 401      : {len(not_401)}")
    print()

    if not_401:
        print("FAILURES (endpoint reachable WITHOUT the shared secret):")
        for r in not_401:
            if r.error is not None:
                print(f"  {r.method:6s} {r.raw_path:80s} ERROR: {r.error}")
            else:
                print(f"  {r.method:6s} {r.raw_path:80s} -> {r.status_code}")
    else:
        print("All 93 endpoints returned 401 with no X-Internal-Service-Key header.")

    return not not_401


def summarize_with_key_sweep(results: list[Result]) -> None:
    """Reporting only, same reasoning as AUTH-003 Part 3's script: a non-2xx
    result here can legitimately be a 404/422 from a placeholder path or an
    empty {} body downstream of the (now-passed) guard, not a guard bug."""
    total = len(results)
    not_401 = [r for r in results if r.status_code != 401]
    still_401 = [r for r in results if r.status_code == 401]

    print()
    print("=" * 78)
    print("AUTH-004 Sweep 2/2 -- CORRECT X-Internal-Service-Key header")
    print("=" * 78)
    print(f"Total endpoints checked      : {total}")
    print(f"Passed the guard (not 401)   : {len(not_401)}")
    print(f"STILL 401 despite correct key: {len(still_401)}")
    print()

    if still_401:
        print("FAILURES (endpoint still 401s even with the correct secret -- guard bug):")
        for r in still_401:
            print(f"  {r.method:6s} {r.raw_path:80s} -> 401")
    else:
        print("All 93 endpoints let the request through (no longer 401) with the correct key.")

    print()
    print("Non-401 status codes below are informational (2xx/404/422 downstream")
    print("of the guard are all normal for placeholder ids / empty {} bodies):")
    for r in not_401:
        if r.error is not None:
            print(f"  {r.method:6s} {r.raw_path:80s} ERROR: {r.error}")
        else:
            print(f"  {r.method:6s} {r.raw_path:80s} -> {r.status_code}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--base-url",
        default="http://localhost:8000",
        help="Base URL of the running server (default: http://localhost:8000)",
    )
    parser.add_argument(
        "--key",
        required=True,
        help="The correct INTERNAL_SERVICE_KEY value to use for sweep 2",
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

    no_key_results = run(args.base_url, args.timeout, headers={})
    sweep1_ok = summarize_no_key_sweep(no_key_results)

    with_key_results = run(
        args.base_url, args.timeout, headers={"X-Internal-Service-Key": args.key}
    )
    summarize_with_key_sweep(with_key_results)

    print()
    if sweep1_ok:
        print("RESULT: PASS -- all 93 endpoints refuse access without the shared secret.")
        return 0
    print("RESULT: FAIL -- see failures above.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
