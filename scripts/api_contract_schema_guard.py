import json
from pathlib import Path
from typing import Any

from app.main import app

DEFAULT_SNAPSHOT_PATH = Path("docs/api_contracts/openapi_snapshot_v1.json")


def load_previous_snapshot(path: Path = DEFAULT_SNAPSHOT_PATH) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"API contract snapshot not found: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def current_openapi() -> dict[str, Any]:
    return app.openapi()


def _schema_signature(value: Any) -> Any:
    if value is None:
        return None

    if isinstance(value, dict):
        return {
            key: _schema_signature(value[key])
            for key in sorted(value.keys())
            if key not in {"description", "example", "examples"}
        }

    if isinstance(value, list):
        return [_schema_signature(item) for item in value]

    return value


def _request_body_signature(operation: dict[str, Any]) -> Any:
    request_body = operation.get("requestBody")
    if not request_body:
        return None

    # Tam OpenAPI formatı:
    # {"content": {"application/json": {"schema": ...}}}
    if isinstance(request_body, dict):
        return _schema_signature(request_body.get("content", {}))

    # Mevcut özet snapshot formatı:
    # ["application/json"] veya ["multipart/form-data"]
    if isinstance(request_body, list):
        return _schema_signature({"media_types": request_body})

    return _schema_signature(request_body)


def _response_signature(operation: dict[str, Any]) -> dict[str, Any]:
    responses = operation.get("responses", {})

    # Mevcut özet snapshot formatı:
    # ["200", "422"]
    if isinstance(responses, list):
        return {
            str(status_code): {"summary_only": True}
            for status_code in sorted(responses)
        }

    if not isinstance(responses, dict):
        return {}

    # Tam OpenAPI formatı:
    # {"200": {"content": {"application/json": {"schema": ...}}}}
    return {
        str(status_code): _schema_signature(response.get("content", {}))
        for status_code, response in sorted(responses.items())
        if isinstance(response, dict)
    }


def _operation_signatures(openapi: dict[str, Any]) -> dict[str, dict[str, Any]]:
    signatures: dict[str, dict[str, Any]] = {}

    for path, methods in openapi.get("paths", {}).items():
        for method, operation in methods.items():
            if method.lower() not in {"get", "post", "put", "patch", "delete"}:
                continue

            key = f"{method.upper()} {path}"
            signatures[key] = {
                "request_body": _request_body_signature(operation),
                "responses": _response_signature(operation),
            }

    return signatures


def _is_summary_request_body(signature: Any) -> bool:
    return (
        isinstance(signature, dict)
        and set(signature.keys()) == {"media_types"}
        and isinstance(signature.get("media_types"), list)
    )


def _media_types_from_request_signature(signature: Any) -> set[str]:
    if signature is None:
        return set()

    if _is_summary_request_body(signature):
        return set(signature["media_types"])

    if isinstance(signature, dict):
        return set(signature.keys())

    return set()


def _is_summary_response(signature: Any) -> bool:
    return signature == {"summary_only": True}


def compare_schema_contract(previous: dict[str, Any], current: dict[str, Any]) -> list[dict[str, Any]]:
    breaking_changes: list[dict[str, Any]] = []

    previous_ops = _operation_signatures(previous)
    current_ops = _operation_signatures(current)

    for key, previous_signature in sorted(previous_ops.items()):
        if key not in current_ops:
            # Path/method kaldırma kontrolü mevcut api_contract_snapshot.py tarafından yapılıyor.
            continue

        current_signature = current_ops[key]

        previous_request = previous_signature["request_body"]
        current_request = current_signature["request_body"]

        # Eski snapshot sadece media type biliyorsa, schema farkı değil yalnızca media type farkı aranır.
        # Test uyumluluğu için bu da REQUEST_BODY_SCHEMA_CHANGED adıyla raporlanır.
        if _is_summary_request_body(previous_request):
            previous_media_types = set(previous_request["media_types"])
            current_media_types = _media_types_from_request_signature(current_request)

            if previous_media_types != current_media_types:
                breaking_changes.append(
                    {
                        "operation": key,
                        "change": "REQUEST_BODY_SCHEMA_CHANGED",
                        "previous": previous_request,
                        "current": current_request,
                        "detail": "REQUEST_MEDIA_TYPE_CHANGED",
                    }
                )

        elif previous_request != current_request:
            # Eski snapshot tam schema içeriyorsa gerçek schema farkı aranır.
            breaking_changes.append(
                {
                    "operation": key,
                    "change": "REQUEST_BODY_SCHEMA_CHANGED",
                    "previous": previous_request,
                    "current": current_request,
                }
            )

        previous_responses = previous_signature["responses"]
        current_responses = current_signature["responses"]

        for status_code, previous_response in sorted(previous_responses.items()):
            if status_code not in current_responses:
                breaking_changes.append(
                    {
                        "operation": key,
                        "status_code": status_code,
                        "change": "RESPONSE_STATUS_SCHEMA_REMOVED",
                    }
                )
                continue

            current_response = current_responses[status_code]

            # Eski snapshot response schema bilmiyorsa, sadece status code varlığı korunur.
            if _is_summary_response(previous_response):
                continue

            if previous_response != current_response:
                breaking_changes.append(
                    {
                        "operation": key,
                        "status_code": status_code,
                        "change": "RESPONSE_SCHEMA_CHANGED",
                        "previous": previous_response,
                        "current": current_response,
                    }
                )

    return breaking_changes


def assert_no_schema_breaking_changes(
    previous: dict[str, Any] | None = None,
    current: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    previous = previous or load_previous_snapshot()
    current = current or current_openapi()

    breaking_changes = compare_schema_contract(previous=previous, current=current)

    if breaking_changes:
        raise AssertionError(
            "Breaking API schema contract changes detected: "
            + json.dumps(breaking_changes, indent=2, ensure_ascii=False)
        )

    return breaking_changes


if __name__ == "__main__":
    assert_no_schema_breaking_changes()
    print("API schema contract guard passed.")
