import json
from pathlib import Path

SNAPSHOT_PATH = Path("docs/api_contracts/openapi_snapshot_v1.json")


def extract_contract(openapi: dict) -> dict:
    paths = openapi.get("paths", {})

    contract_paths = {}

    for path, methods in sorted(paths.items()):
        contract_paths[path] = {
            method: {
                "operationId": spec.get("operationId"),
                "tags": spec.get("tags", []),
                "summary": spec.get("summary"),
                "requestBody": _compact_request_body(spec.get("requestBody")),
                "responses": sorted((spec.get("responses") or {}).keys()),
            }
            for method, spec in sorted(methods.items())
            if method in {"get", "post", "put", "patch", "delete"}
        }

    return {
        "version": "v1",
        "path_count": len(contract_paths),
        "paths": contract_paths,
    }


def _compact_request_body(request_body):
    if not request_body:
        return None

    content = request_body.get("content", {})
    return sorted(content.keys())


def save_contract_snapshot(openapi: dict, path: Path = SNAPSHOT_PATH) -> dict:
    contract = extract_contract(openapi)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(contract, ensure_ascii=False, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    return contract


def load_contract_snapshot(path: Path = SNAPSHOT_PATH) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def compare_contracts(*, previous: dict, current: dict) -> dict:
    previous_paths = set(previous.get("paths", {}))
    current_paths = set(current.get("paths", {}))

    removed_paths = sorted(previous_paths - current_paths)
    added_paths = sorted(current_paths - previous_paths)

    changed_operations = []

    for path in sorted(previous_paths & current_paths):
        previous_methods = previous["paths"][path]
        current_methods = current["paths"][path]

        removed_methods = sorted(set(previous_methods) - set(current_methods))
        added_methods = sorted(set(current_methods) - set(previous_methods))

        for method in removed_methods:
            changed_operations.append(
                {
                    "path": path,
                    "method": method,
                    "change": "REMOVED_METHOD",
                }
            )

        for method in added_methods:
            changed_operations.append(
                {
                    "path": path,
                    "method": method,
                    "change": "ADDED_METHOD",
                }
            )

        for method in sorted(set(previous_methods) & set(current_methods)):
            previous_operation = previous_methods[method]
            current_operation = current_methods[method]

            if previous_operation.get("operationId") != current_operation.get("operationId"):
                changed_operations.append(
                    {
                        "path": path,
                        "method": method,
                        "change": "OPERATION_ID_CHANGED",
                        "previous": previous_operation.get("operationId"),
                        "current": current_operation.get("operationId"),
                    }
                )

            previous_responses = set(previous_operation.get("responses", []))
            current_responses = set(current_operation.get("responses", []))
            removed_responses = sorted(previous_responses - current_responses)
            if removed_responses:
                changed_operations.append(
                    {
                        "path": path,
                        "method": method,
                        "change": "RESPONSES_REMOVED",
                        "removed": removed_responses,
                    }
                )

    breaking_changes = [
        *[
            {
                "path": path,
                "change": "REMOVED_PATH",
            }
            for path in removed_paths
        ],
        *[
            change
            for change in changed_operations
            if change["change"] in {
                "REMOVED_METHOD",
                "OPERATION_ID_CHANGED",
                "RESPONSES_REMOVED",
            }
        ],
    ]

    return {
        "breaking_change_count": len(breaking_changes),
        "breaking_changes": breaking_changes,
        "added_paths": added_paths,
        "removed_paths": removed_paths,
        "changed_operations": changed_operations,
    }


def assert_no_breaking_changes(*, previous: dict, current: dict) -> dict:
    comparison = compare_contracts(previous=previous, current=current)

    if comparison["breaking_change_count"] > 0:
        raise AssertionError(
            "Breaking API contract changes detected: "
            + json.dumps(comparison["breaking_changes"], ensure_ascii=False, indent=2)
        )

    return comparison


if __name__ == "__main__":
    from app.main import app

    current = extract_contract(app.openapi())

    if not SNAPSHOT_PATH.exists():
        save_contract_snapshot(app.openapi(), SNAPSHOT_PATH)
        print(f"API contract snapshot created: {SNAPSHOT_PATH}")
    else:
        previous = load_contract_snapshot(SNAPSHOT_PATH)
        comparison = assert_no_breaking_changes(previous=previous, current=current)
        print(
            "API contract snapshot check passed. "
            f"Added paths: {len(comparison['added_paths'])}. "
            f"Breaking changes: {comparison['breaking_change_count']}."
        )
