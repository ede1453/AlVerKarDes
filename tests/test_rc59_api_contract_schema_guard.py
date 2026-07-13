import copy

import pytest

from scripts.api_contract_schema_guard import (
    assert_no_schema_breaking_changes,
    compare_schema_contract,
    current_openapi,
)


def test_rc59_schema_guard_passes_against_current_snapshot():
    assert assert_no_schema_breaking_changes() == []


def test_rc59_schema_guard_detects_request_body_schema_change():
    previous = current_openapi()
    current = copy.deepcopy(previous)

    candidate = None
    for _path, methods in current["paths"].items():
        for method, operation in methods.items():
            if method == "post" and "requestBody" in operation:
                candidate = operation
                break
        if candidate:
            break

    assert candidate is not None

    content = candidate["requestBody"]["content"]
    first_media = next(iter(content))
    content[first_media]["schema"] = {"type": "object", "properties": {"breaking": {"type": "string"}}}

    changes = compare_schema_contract(previous=previous, current=current)

    assert any(change["change"] == "REQUEST_BODY_SCHEMA_CHANGED" for change in changes)


def test_rc59_schema_guard_detects_response_schema_change():
    previous = current_openapi()
    current = copy.deepcopy(previous)

    candidate = None
    for _path, methods in current["paths"].items():
        for _method, operation in methods.items():
            responses = operation.get("responses", {})
            if "200" in responses and responses["200"].get("content"):
                candidate = responses["200"]
                break
        if candidate:
            break

    assert candidate is not None

    first_media = next(iter(candidate["content"]))
    candidate["content"][first_media]["schema"] = {"type": "object", "properties": {"changed": {"type": "boolean"}}}

    changes = compare_schema_contract(previous=previous, current=current)

    assert any(change["change"] == "RESPONSE_SCHEMA_CHANGED" for change in changes)


def test_rc59_schema_guard_raises_on_breaking_change():
    previous = current_openapi()
    current = copy.deepcopy(previous)

    candidate = None
    for _path, methods in current["paths"].items():
        for method, operation in methods.items():
            if method == "post" and "requestBody" in operation:
                candidate = operation
                break
        if candidate:
            break

    assert candidate is not None

    content = candidate["requestBody"]["content"]
    first_media = next(iter(content))
    content[first_media]["schema"] = {"type": "string"}

    with pytest.raises(AssertionError):
        assert_no_schema_breaking_changes(previous=previous, current=current)