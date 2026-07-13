from scripts.api_contract_schema_guard import (
    _operation_signatures,
    assert_no_schema_breaking_changes,
    compare_schema_contract,
)


def test_rc591_schema_guard_accepts_summary_snapshot_request_body_and_responses():
    snapshot = {
        "paths": {
            "/api/v1/admin/import/upload": {
                "post": {
                    "operationId": "upload_feed_api_v1_admin_import_upload_post",
                    "requestBody": ["multipart/form-data"],
                    "responses": ["200", "422"],
                }
            }
        }
    }

    signatures = _operation_signatures(snapshot)

    assert signatures["POST /api/v1/admin/import/upload"]["request_body"] == {
        "media_types": ["multipart/form-data"]
    }
    assert signatures["POST /api/v1/admin/import/upload"]["responses"] == {
        "200": {"summary_only": True},
        "422": {"summary_only": True},
    }


def test_rc591_schema_guard_does_not_crash_on_existing_snapshot_format():
    assert assert_no_schema_breaking_changes() == []


def test_rc591_schema_guard_detects_summary_snapshot_media_type_change():
    previous = {
        "paths": {
            "/api/v1/example": {
                "post": {
                    "requestBody": ["application/json"],
                    "responses": ["200"],
                }
            }
        }
    }
    current = {
        "paths": {
            "/api/v1/example": {
                "post": {
                    "requestBody": ["multipart/form-data"],
                    "responses": ["200"],
                }
            }
        }
    }

    changes = compare_schema_contract(previous=previous, current=current)

    assert any(change["change"] == "REQUEST_BODY_SCHEMA_CHANGED" for change in changes)
