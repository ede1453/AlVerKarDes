from __future__ import annotations

import http.client
import json
import socket
import sys
import time
import urllib.error
import urllib.request

BASE_URL = (
    sys.argv[1].rstrip("/")
    if len(sys.argv) > 1
    else "http://127.0.0.1:8000"
)

MAX_ATTEMPTS = 60
WAIT_SECONDS = 2

if "YOUR_DOMAIN" in BASE_URL.upper():
    raise SystemExit(
        "Replace YOUR_DOMAIN with a real domain, "
        "or use http://127.0.0.1:8000."
    )

checks = [
    "/health",
    "/openapi.json",
]


def get(path: str) -> tuple[int, str]:
    url = BASE_URL + path

    request = urllib.request.Request(
        url,
        headers={
            "Connection": "close",
            "User-Agent": "aici-production-smoke/1.0",
        },
    )

    with urllib.request.urlopen(
        request,
        timeout=10,
    ) as response:
        return (
            response.status,
            response.read().decode("utf-8"),
        )


retryable_errors = (
    urllib.error.URLError,
    urllib.error.HTTPError,
    http.client.RemoteDisconnected,
    ConnectionResetError,
    ConnectionRefusedError,
    TimeoutError,
    socket.timeout,
    OSError,
)

last_error: Exception | None = None

for attempt in range(1, MAX_ATTEMPTS + 1):
    try:
        status, _ = get("/health")

        if status == 200:
            print(
                json.dumps(
                    {
                        "base_url": BASE_URL,
                        "path": "/health",
                        "status": status,
                        "attempt": attempt,
                    }
                )
            )
            break
    except retryable_errors as exc:
        last_error = exc

    print(
        f"Waiting for production API "
        f"({attempt}/{MAX_ATTEMPTS}): "
        f"{type(last_error).__name__ if last_error else 'not ready'}"
    )
    time.sleep(WAIT_SECONDS)
else:
    raise SystemExit(
        f"Production API did not become ready at "
        f"{BASE_URL}: {last_error}"
    )

for path in checks:
    try:
        status, body = get(path)
    except retryable_errors as exc:
        raise SystemExit(
            f"Smoke test failed for "
            f"{BASE_URL + path}: {type(exc).__name__}: {exc}"
        ) from exc

    if status != 200:
        raise SystemExit(
            f"{path} failed: {status}"
        )

    print(
        json.dumps(
            {
                "base_url": BASE_URL,
                "path": path,
                "status": status,
            }
        )
    )

print("Production smoke tests passed.")
