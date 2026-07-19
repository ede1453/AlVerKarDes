from __future__ import annotations

from scripts.validate_release_manifest import main, validate_manifest


def _valid_manifest() -> dict:
    return {
        "version": "v1.0.0",
        "commit_sha": "abc123",
        "source_digest_sha256": "a" * 64,
        "generated_at": "2026-07-15T00:00:00+00:00",
        "release_status": "RELEASE_CANDIDATE_APPROVED",
        "production_port": 8000,
        "alembic_head": "0014_deal_storage_sqlalchemy",
        "connector_readiness": {
            "status": "ACTION_REQUIRED",
            "summary": {
                "connector_count": 2,
                "operational_ready_count": 1,
                "production_ready_count": 0,
                "mock_or_fixture_count": 1,
                "action_required_count": 1,
            },
            "connectors": [
                {
                    "connector_id": "mock_marketplace",
                    "mode": "mock",
                    "operational_ready": True,
                    "production_ready": False,
                    "missing_required_env": [],
                },
                {
                    "connector_id": "amazon_creators",
                    "mode": "production",
                    "operational_ready": False,
                    "production_ready": False,
                    "missing_required_env": ["AMAZON_CREATORS_CLIENT_ID"],
                },
            ],
        },
    }


def test_validate_release_manifest_accepts_current_contract():
    assert validate_manifest(_valid_manifest()) == []


def test_validate_release_manifest_rejects_wrong_port_and_summary():
    manifest = _valid_manifest()
    manifest["production_port"] = 18000
    manifest["connector_readiness"]["summary"]["connector_count"] = 99

    errors = validate_manifest(manifest)

    assert "production_port must be 8000" in errors
    assert "summary.connector_count does not match connectors length" in errors


def test_validate_release_manifest_rejects_env_values_in_missing_env_names():
    manifest = _valid_manifest()
    manifest["connector_readiness"]["connectors"][1]["missing_required_env"] = [
        "secret-value-123"
    ]

    errors = validate_manifest(manifest)

    assert any("invalid env name" in error for error in errors)


def test_validate_release_manifest_cli_reads_manifest_file(capsys):
    manifest_path = __import__("pathlib").Path("release/_test_manifest_validation.json")
    manifest_path.write_text(
        __import__("json").dumps(_valid_manifest()),
        encoding="utf-8",
    )
    try:
        exit_code = main([str(manifest_path)])
    finally:
        manifest_path.unlink(missing_ok=True)

    assert exit_code == 0
    assert "Release manifest validation passed." in capsys.readouterr().out
