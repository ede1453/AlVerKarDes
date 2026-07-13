import pytest

from scripts.api_contract_snapshot import assert_no_breaking_changes, compare_contracts


def test_api_contract_snapshot_allows_added_paths():
    previous = {
        "paths": {
            "/api/v1/a": {
                "get": {
                    "operationId": "getA",
                    "responses": ["200"],
                }
            }
        }
    }
    current = {
        "paths": {
            "/api/v1/a": {
                "get": {
                    "operationId": "getA",
                    "responses": ["200"],
                }
            },
            "/api/v1/b": {
                "get": {
                    "operationId": "getB",
                    "responses": ["200"],
                }
            },
        }
    }

    comparison = assert_no_breaking_changes(previous=previous, current=current)

    assert comparison["breaking_change_count"] == 0
    assert comparison["added_paths"] == ["/api/v1/b"]


def test_api_contract_snapshot_detects_removed_path():
    previous = {
        "paths": {
            "/api/v1/a": {
                "get": {
                    "operationId": "getA",
                    "responses": ["200"],
                }
            }
        }
    }
    current = {"paths": {}}

    comparison = compare_contracts(previous=previous, current=current)

    assert comparison["breaking_change_count"] == 1
    assert comparison["breaking_changes"][0]["change"] == "REMOVED_PATH"

    with pytest.raises(AssertionError):
        assert_no_breaking_changes(previous=previous, current=current)


def test_api_contract_snapshot_detects_operation_id_change():
    previous = {
        "paths": {
            "/api/v1/a": {
                "get": {
                    "operationId": "getA",
                    "responses": ["200"],
                }
            }
        }
    }
    current = {
        "paths": {
            "/api/v1/a": {
                "get": {
                    "operationId": "getAChanged",
                    "responses": ["200"],
                }
            }
        }
    }

    comparison = compare_contracts(previous=previous, current=current)

    assert comparison["breaking_change_count"] == 1
    assert comparison["breaking_changes"][0]["change"] == "OPERATION_ID_CHANGED"
